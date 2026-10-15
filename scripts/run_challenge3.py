"""Run Challenge 3 (Tesla Risk Assessment) and save the research result."""

import json
import logging
from pathlib import Path

from agent.core import create_agent
from llm.client import LLMClient

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"

QUERY = (
    "Produce a comprehensive risk assessment for Tesla Inc. covering "
    "financial risks, operational risks, regulatory risks, and competitive risks. "
    "Use sec_edgar, web_search, news_sentiment, financial_api, and earnings_transcript "
    "where appropriate. Quantify risks where possible and distinguish sourced facts "
    "from speculation. Do not fabricate figures or citations."
)

ALLOWED_TOOLS = {
    "sec_edgar",
    "web_search",
    "news_sentiment",
    "financial_api",
    "earnings_transcript",
    "company_profile",
    "calculation_engine",
}


def main() -> None:
    """Execute Challenge 3 and persist its result."""
    logging.basicConfig(level=logging.INFO)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    llm_client = LLMClient(model="groq/qwen/qwen3.8-27b")
    agent = create_agent(
        max_iterations=4,
        max_tokens=1000,
        allowed_tools=ALLOWED_TOOLS,
        llm_client=llm_client,
    )

    print(f"\n=======================================================")
    print(f"Executing Challenge 3: Tesla Risk Assessment")
    print(f"Query: {QUERY}")
    print(f"Allowed Tools: {ALLOWED_TOOLS}")
    print(f"=======================================================\n")

    try:
        result = agent.run(QUERY)
    except Exception as exc:
        logging.exception("Challenge 3 failed")
        result = {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    output_path = RESULTS_DIR / "challenge_3_raw.json"
    output_path.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    print(f"\n-------------------------------------------------------")
    print(f"Execution Completed!")
    print(f"Result saved to: {output_path}")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Iterations: {result.get('iterations', 'unknown')}")
    print(f"Error: {result.get('error', 'none')}")

    tool_calls = result.get("tool_calls", [])
    print(f"Tools invoked ({len(tool_calls)}): {[call.get('tool') for call in tool_calls]}")

    answer = result.get("answer", "")
    if answer:
        print("\nResearch Output Summary:\n")
        print(answer[:2500])
    print(f"-------------------------------------------------------\n")


if __name__ == "__main__":
    main()
