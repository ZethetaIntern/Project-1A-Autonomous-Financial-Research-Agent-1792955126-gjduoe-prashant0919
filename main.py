"""Autonomous Financial Research Agent (ARA-1) - Unified CLI Entry Point.

QuantumEdge Research / Zetheta Algorithms Private Limited
Project 1A: Autonomous Financial Research Agent with Multi-Source Synthesis
Author: Prashant Bastola (bastolaprashant0919@gmail.com)
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from agent.core import create_agent
from config.logging_config import setup_logging
from evaluation.dashboard import generate_evaluation_summary
from llm.client import LLMClient

ROOT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = ROOT_DIR / "results"

CHALLENGE_QUERIES = {
    1: {
        "title": "Challenge 1: Microsoft Corporation Company Profile",
        "query": (
            "Create a comprehensive profile of Microsoft Corporation covering its business "
            "overview, financial summary, key executives, and recent developments. "
            "Use company_profile, financial_api, and web_search where appropriate. "
            "Distinguish sourced facts from unavailable information. Do not invent figures or citations."
        ),
        "tools": {"company_profile", "financial_api", "web_search"},
        "result_md": "challenge_1.md",
        "result_json": "challenge_1_raw.json",
    },
    2: {
        "title": "Challenge 2: Apple Inc. Q3 Earnings Analysis",
        "query": (
            "Conduct an in-depth earnings analysis of Apple Inc.'s latest quarterly performance. "
            "Analyze revenue growth, segment breakdowns, gross margins, and forward guidance. "
            "Use earnings_transcript, financial_api, sec_edgar, and calculation_engine where appropriate."
        ),
        "tools": {"earnings_transcript", "financial_api", "sec_edgar", "calculation_engine"},
        "result_md": "challenge_2.md",
        "result_json": "challenge_2_raw.json",
    },
    3: {
        "title": "Challenge 3: Tesla Inc. Comprehensive Risk Assessment",
        "query": (
            "Produce a comprehensive risk assessment for Tesla Inc. covering financial risks, "
            "operational risks, regulatory risks, and competitive risks. "
            "Use sec_edgar, web_search, news_sentiment, financial_api, and earnings_transcript "
            "where appropriate. Quantify risks where possible and distinguish sourced facts from speculation."
        ),
        "tools": {
            "sec_edgar",
            "web_search",
            "news_sentiment",
            "financial_api",
            "earnings_transcript",
            "company_profile",
            "calculation_engine",
        },
        "result_md": "challenge_3.md",
        "result_json": "challenge_3_raw.json",
    },
    4: {
        "title": "Challenge 4: Cloud Hyperscalers Comparison (AWS vs Azure vs GCP)",
        "query": (
            "Synthesize an industry comparative analysis for Cloud Hyperscalers comparing Amazon AWS, "
            "Microsoft Azure, and Google Cloud Platform across revenue run-rates, growth trajectories, "
            "operating margins, AI infrastructure, and enterprise positioning."
        ),
        "tools": {"peer_comparison", "financial_api", "web_search", "calculation_engine"},
        "result_md": "challenge_4.md",
        "result_json": "challenge_4_raw.json",
    },
    5: {
        "title": "Challenge 5: Palantir Contradictory Data Investigation",
        "query": (
            "Investigate Palantir Technologies (PLTR) revenue, margin, and operating guidance discrepancies "
            "between GAAP filings, non-GAAP executive commentary, and social sentiment. Apply the 6-step "
            "conflict resolution protocol and fact_checker to resolve discrepancies."
        ),
        "tools": {"company_profile", "financial_api", "fact_checker", "sec_edgar", "news_sentiment"},
        "result_md": "challenge_5.md",
        "result_json": "challenge_5_raw.json",
    },
    6: {
        "title": "Challenge 6: Ambiguous Query: 'What's happening with the banks?'",
        "query": "What's happening with the banks?",
        "tools": {"financial_api", "news_sentiment", "web_search", "company_profile"},
        "result_md": "challenge_6.md",
        "result_json": "challenge_6_raw.json",
    },
    7: {
        "title": "Challenge 7: Tech Sector Synthesis with Vector Memory",
        "query": (
            "Synthesize cross-company thematic research across Big Tech using vector memory store "
            "and similarity search across previously analyzed entities (MSFT, AAPL, AMZN, GOOGL, NVDA)."
        ),
        "tools": {"vector_db_search", "vector_db_store", "peer_comparison", "financial_api"},
        "result_md": "challenge_7.md",
        "result_json": "challenge_7_raw.json",
    },
    8: {
        "title": "Challenge 8: NVIDIA Institutional Report under 50% Tool Degradation",
        "query": (
            "Generate an institutional research report on NVIDIA Corporation (NVDA) evaluating Blackwell "
            "architecture demand, DCF valuation, and data center revenue momentum while operating under "
            "a simulated 50% tool failure rate using fallback chains and graceful degradation."
        ),
        "tools": {"company_profile", "financial_api", "calculation_engine", "sec_edgar", "fact_checker"},
        "result_md": "challenge_8.md",
        "result_json": "challenge_8_raw.json",
    },
}


def run_agent_challenge(challenge_num: int, max_iterations: int = 4) -> dict[str, Any]:
    """Execute a specific challenge with the autonomous agent."""
    cfg = CHALLENGE_QUERIES.get(challenge_num)
    if not cfg:
        print(f"Error: Unknown challenge number {challenge_num}. Choose 1 to 8.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print(f"Executing {cfg['title']}")
    print(f"Query: {cfg['query']}")
    print(f"Allowed Tools: {sorted(cfg['tools'])}")
    print("=" * 70 + "\n")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    agent = create_agent(
        max_iterations=max_iterations,
        max_tokens=1500,
        allowed_tools=cfg["tools"],
    )

    try:
        result = agent.run(cfg["query"])
    except Exception as exc:
        logging.exception("Challenge execution failed")
        result = {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    raw_path = RESULTS_DIR / cfg["result_json"]
    raw_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    print("\n" + "-" * 70)
    print("Execution Finished!")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Iterations: {result.get('iterations', 'unknown')}")
    tool_calls = result.get("tool_calls", [])
    print(f"Tools Invoked ({len(tool_calls)}): {[c.get('tool') for c in tool_calls]}")
    print(f"Raw Output Persisted: {raw_path}")

    answer = result.get("answer", "")
    if answer:
        print("\nResearch Output Summary:\n")
        print(answer[:2000])
        if len(answer) > 2000:
            print("\n... [Full response saved in JSON] ...")
    print("-" * 70 + "\n")

    md_report = RESULTS_DIR / cfg["result_md"]
    if md_report.exists():
        print(f"Comprehensive Institutional Markdown Report: {md_report}")

    return result


def run_custom_query(query: str, max_iterations: int = 4) -> dict[str, Any]:
    """Execute an arbitrary user query with full tool registry."""
    print("\n" + "=" * 70)
    print("Executing Custom Financial Research Query")
    print(f"Query: {query}")
    print("=" * 70 + "\n")

    agent = create_agent(
        max_iterations=max_iterations,
        max_tokens=1500,
    )

    result = agent.run(query)

    print("\n" + "-" * 70)
    print("Execution Finished!")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Iterations: {result.get('iterations', 'unknown')}")
    tool_calls = result.get("tool_calls", [])
    print(f"Tools Invoked ({len(tool_calls)}): {[c.get('tool') for c in tool_calls]}")

    answer = result.get("answer", "")
    if answer:
        print("\nResearch Output:\n")
        print(answer)
    print("-" * 70 + "\n")

    return result


def run_tests() -> int:
    """Run full pytest test suite."""
    print("\n=======================================================")
    print("Running Complete Pytest Suite (Unit + Integration Tests)")
    print("=======================================================\n")
    venv_pytest = ROOT_DIR / ".venv" / "bin" / "pytest"
    cmd = [str(venv_pytest) if venv_pytest.exists() else "pytest", "-v"]
    return subprocess.call(cmd)


def run_eval() -> None:
    """Run evaluation framework across all 8 challenges."""
    print("\n=======================================================")
    print("Running Research Quality Board (RQB) Evaluation Dashboard")
    print("=======================================================\n")
    summary = generate_evaluation_summary()
    print("Evaluation Summary:")
    print(f"Status: {summary.get('status')}")
    print(f"Composite RQB Quality Score: {summary.get('composite_rqb_score'):.2f} / 100")
    print(f"Evaluated Challenges: {summary.get('reports_count')} / 8")
    print("\nScorecards Generated:")
    print(f"- Markdown: {RESULTS_DIR / 'evaluation_report.md'}")
    print(f"- Documentation: {ROOT_DIR / 'docs' / 'evaluation_report_final.md'}")
    print(f"- HTML Visual Dashboard: {RESULTS_DIR / 'evaluation_report.html'}")


def main() -> None:
    """CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Autonomous Financial Research Agent with Multi-Source Synthesis (ARA-1)"
    )
    parser.add_argument(
        "--challenge",
        "-c",
        type=int,
        choices=range(1, 9),
        help="Execute one of the 8 progressive research challenges (1-8)",
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        help="Execute a custom research query",
    )
    parser.add_argument(
        "--test",
        "-t",
        action="store_true",
        help="Run the complete automated test suite (pytest)",
    )
    parser.add_argument(
        "--eval",
        "-e",
        action="store_true",
        help="Generate the RQB evaluation scorecard across all 8 challenges",
    )
    parser.add_argument(
        "--iterations",
        "-i",
        type=int,
        default=4,
        help="Maximum ReAct agent iterations (default: 4)",
    )

    args = parser.parse_args()

    setup_logging()

    if args.test:
        sys.exit(run_tests())
    elif args.eval:
        run_eval()
    elif args.challenge:
        run_agent_challenge(args.challenge, max_iterations=args.iterations)
    elif args.query:
        run_custom_query(args.query, max_iterations=args.iterations)
    else:
        # Default behavior when run with no arguments: show menu or evaluate
        print("\n" + "=" * 70)
        print("Autonomous Financial Research Agent with Multi-Source Synthesis (ARA-1)")
        print("QuantumEdge Research / Zetheta Algorithms Private Limited")
        print("Author: Prashant Bastola (bastolaprashant0919@gmail.com)")
        print("=" * 70)
        print("\nUsage Options:")
        print("  python main.py --challenge <1-8>  : Run a specific challenge (e.g. --challenge 3)")
        print("  python main.py --query '<query>'  : Run a custom financial research query")
        print("  python main.py --eval             : Generate full RQB evaluation scorecard")
        print("  python main.py --test             : Run complete test suite (49 pytest tests)")
        print("\nAvailable Challenge Reports in results/:")
        for i in range(1, 9):
            cfg = CHALLENGE_QUERIES[i]
            print(f"  [{i}] {cfg['title']}")
        print("\nExecuting default evaluation dashboard...\n")
        run_eval()


if __name__ == "__main__":
    main()
