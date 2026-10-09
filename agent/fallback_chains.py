"""Fallback tool chains and graceful degradation protocol for research execution."""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class FallbackExecutionResult:
    """The outcome of executing a tool or its downstream fallback chain."""

    primary_tool: str
    executed_tool: str
    was_fallback: bool
    fallback_level: int           # 0 = primary succeeded, 1 = first fallback, 2 = second fallback, etc.
    success: bool
    data: Any
    confidence_penalty: float     # e.g., 0.10 penalty for first fallback, 0.25 for second
    effective_confidence: float
    degradation_note: str | None = None
    attempted_tools: list[str] = field(default_factory=list)


# Defined fallback tool chains (Section A4.3)
TOOL_FALLBACK_CHAINS: dict[str, list[str]] = {
    # Financial metrics: financial_api -> sec_edgar -> web_search -> vector_db_search
    "financial_api": ["sec_edgar", "web_search", "vector_db_search"],
    # SEC filings: sec_edgar -> web_search -> vector_db_search
    "sec_edgar": ["web_search", "vector_db_search"],
    # Transcripts: earnings_transcript -> earnings -> web_search
    "earnings_transcript": ["earnings", "web_search"],
    # News sentiment: news_sentiment -> web_search
    "news_sentiment": ["web_search"],
    # Company profile: company_profile -> web_search -> vector_db_search
    "company_profile": ["web_search", "vector_db_search"],
    # Peer comparison: peer_comparison -> financial_api -> web_search
    "peer_comparison": ["financial_api", "web_search"],
    # Calculation engine: calculation_engine -> calculator
    "calculation_engine": ["calculator"],
}


class FallbackChainManager:
    """Orchestrates multi-level tool fallbacks and generates graceful degradation logs."""

    def __init__(self, fallback_chains: dict[str, list[str]] | None = None) -> None:
        self.chains = fallback_chains or dict(TOOL_FALLBACK_CHAINS)
        self.degradation_events: list[FallbackExecutionResult] = []

    def get_fallback_tools(self, primary_tool: str) -> list[str]:
        """Return the sequence of fallback tools for a primary tool."""
        return self.chains.get(primary_tool, [])

    def execute_with_fallback(
        self,
        primary_tool: str,
        tool_executor: Callable[[str, dict[str, Any]], dict[str, Any]],
        arguments: dict[str, Any],
        argument_adapter: Callable[[str, str, dict[str, Any]], dict[str, Any]] | None = None,
    ) -> FallbackExecutionResult:
        """Attempt primary tool, cascading to fallbacks on failure."""
        chain = [primary_tool] + self.get_fallback_tools(primary_tool)
        attempted: list[str] = []

        base_confidence = 1.0

        for level, tool_name in enumerate(chain):
            attempted.append(tool_name)
            # Adapt arguments if necessary for fallback tools
            current_args = arguments
            if level > 0 and argument_adapter:
                current_args = argument_adapter(primary_tool, tool_name, arguments)

            try:
                logger.info("Executing tool in chain: %s (level %d)", tool_name, level)
                result = tool_executor(tool_name, current_args)

                # Check if tool execution was successful
                if isinstance(result, dict) and result.get("success") is not False and not result.get("error"):
                    penalty = level * 0.15
                    eff_confidence = max(0.40, base_confidence - penalty)

                    degradation_note = None
                    if level > 0:
                        degradation_note = (
                            f"Primary tool '{primary_tool}' failed. Fallback tool '{tool_name}' "
                            f"(level {level}) was invoked with {penalty:.0%} confidence penalty."
                        )

                    out = FallbackExecutionResult(
                        primary_tool=primary_tool,
                        executed_tool=tool_name,
                        was_fallback=level > 0,
                        fallback_level=level,
                        success=True,
                        data=result.get("data") if isinstance(result, dict) else result,
                        confidence_penalty=penalty,
                        effective_confidence=eff_confidence,
                        degradation_note=degradation_note,
                        attempted_tools=attempted,
                    )
                    if level > 0:
                        self.degradation_events.append(out)
                    return out

                logger.warning("Tool '%s' returned failure in fallback chain: %s", tool_name, result.get("error"))

            except Exception as exc:
                logger.warning("Tool '%s' raised exception in fallback chain: %s", tool_name, exc)

        # Total degradation: All fallbacks failed
        final_note = (
            f"Graceful Degradation Notice: Primary tool '{primary_tool}' and all fallbacks "
            f"({', '.join(chain[1:])}) failed. Sourced metrics for this section were omitted "
            f"to uphold zero hallucination policy. Suggest manual lookup or alternative API integration."
        )
        failure_result = FallbackExecutionResult(
            primary_tool=primary_tool,
            executed_tool="none",
            was_fallback=True,
            fallback_level=len(chain),
            success=False,
            data=None,
            confidence_penalty=1.0,
            effective_confidence=0.0,
            degradation_note=final_note,
            attempted_tools=attempted,
        )
        self.degradation_events.append(failure_result)
        return failure_result

    def generate_graceful_degradation_report(self) -> str:
        """Produce markdown disclosure of all fallback events and omissions (Section A4.3)."""
        if not self.degradation_events:
            return "No tool failures occurred during this research session. All primary sources executed normally."

        lines = [
            "### Graceful Degradation & Data Integrity Disclosures",
            "The autonomous agent encountered tool or network issues and engaged the following fallback chains:",
            "",
        ]

        for ev in self.degradation_events:
            lines.append(
                f"- **Primary Tool:** `{ev.primary_tool}` | **Executed:** `{ev.executed_tool}` "
                f"(Fallback Level {ev.fallback_level}) | **Confidence:** {ev.effective_confidence:.0%}"
            )
            if ev.degradation_note:
                lines.append(f"  *Note:* {ev.degradation_note}")

        return "\n".join(lines)
