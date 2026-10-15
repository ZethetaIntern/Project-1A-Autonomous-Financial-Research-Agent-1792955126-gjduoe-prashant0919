"""Parse LLM responses into tool calls or final answers."""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class ResponseParseError(ValueError):
    """Raised when an LLM response cannot be parsed safely."""


@dataclass
class ParsedResponse:
    """Represent a parsed agent response."""

    response_type: str
    content: str = ""
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None


def parse_response(text: str) -> ParsedResponse:
    """Parse a JSON tool call, JSON final answer, or plain-text answer."""

    if not isinstance(text, str) or not text.strip():
        raise ResponseParseError("LLM response cannot be empty.")

    cleaned = text.strip()

    # Extract content from XML tool tags if present (e.g. <tool_call>...</tool_call> or <action>...</action>)
    xml_match = re.search(
        r"<(?:tool_call|action)>(.*?)</(?:tool_call|action)>",
        cleaned,
        re.DOTALL | re.IGNORECASE,
    )
    if xml_match:
        cleaned = xml_match.group(1).strip()
    else:
        # Strip unclosed or isolated tags if present at edges
        cleaned = re.sub(r"^<(?:tool_call|action)>\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*</(?:tool_call|action)>$", "", cleaned, flags=re.IGNORECASE).strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) < 3 or not lines[-1].strip().startswith("```"):
            raise ResponseParseError("Markdown code fence is not properly closed.")
        cleaned = "\n".join(lines[1:-1]).strip()

    # Handle inner code fences if previously wrapped in XML tags
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3 and lines[-1].strip().startswith("```"):
            cleaned = "\n".join(lines[1:-1]).strip()

    # Check for embedded json code fence if text contains surrounding commentary
    if not cleaned.startswith("{") and "```" in cleaned:
        code_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if code_match:
            candidate = code_match.group(1).strip()
            try:
                test_payload = json.loads(candidate)
                if isinstance(test_payload, dict) and any(
                    k in test_payload for k in ("action", "tool_call", "name", "type")
                ):
                    cleaned = candidate
            except json.JSONDecodeError:
                pass

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Recover gracefully if a final answer JSON was truncated mid-string by token limits
        answer_match = re.search(r'["\']answer["\']\s*:\s*["\'](.*)', cleaned, re.DOTALL)
        if answer_match:
            recovered = answer_match.group(1).rstrip()
            recovered = re.sub(r'["\']\s*\}?\s*$', '', recovered)
            recovered = (
                recovered.replace('\\n', '\n')
                .replace('\\"', '"')
                .replace('\\t', '\t')
            )
            if recovered.strip():
                return ParsedResponse(response_type="final", content=recovered.strip())

        if cleaned.startswith(("{", "[")):
            raise ResponseParseError("LLM returned malformed JSON.") from exc
        return ParsedResponse(response_type="final", content=cleaned)

    if not isinstance(payload, dict):
        raise ResponseParseError("JSON response must be an object.")

    # Preferred format: {"action": "execute", "name": ..., "arguments": ...}
    # Legacy format remains supported: {"tool_call": {...}}
    # Direct format supported: {"name": ..., "arguments": {...}}
    if payload.get("action") == "execute":
        name = payload.get("name")
        arguments = payload.get("arguments", {})
    elif "tool_call" in payload:
        call = payload["tool_call"]
        if not isinstance(call, dict):
            raise ResponseParseError("'tool_call' must be an object.")
        name = call.get("name")
        arguments = call.get("arguments", {})
    elif "name" in payload and isinstance(payload.get("arguments"), dict):
        name = payload.get("name")
        arguments = payload.get("arguments", {})
    else:
        name = None
        arguments = {}

    if payload.get("action") == "final" or payload.get("type") == "final":
        answer = payload.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise ResponseParseError("Final response requires a non-empty answer.")
        return ParsedResponse(response_type="final", content=answer.strip())

    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ResponseParseError("Tool call requires a non-empty name.")
        if not isinstance(arguments, dict):
            raise ResponseParseError("Tool arguments must be a JSON object.")
        return ParsedResponse(
            response_type="tool_call",
            tool_name=name.strip(),
            arguments=arguments,
        )

    raise ResponseParseError(
        "JSON response must contain an execute action, a tool_call, or a final answer."
    )
