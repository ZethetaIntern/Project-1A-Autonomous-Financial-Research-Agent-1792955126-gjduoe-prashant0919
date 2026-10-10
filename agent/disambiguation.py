"""Disambiguation logic, documented assumptions, and financial edge case handling."""

import logging
from dataclasses import dataclass, field
from typing import Any

from agent.query_analyzer import QueryAnalysis, QueryType

logger = logging.getLogger(__name__)


@dataclass
class DisambiguationResult:
    """The result of disambiguating an ambiguous query or financial edge case."""

    original_query: str
    is_ambiguous: bool
    ambiguity_reasons: list[str]
    clarifying_questions: list[str]
    documented_assumptions: list[str]
    focused_scope: str
    edge_case_type: str | None = None  # 'private_company', 'recent_ipo', 'rapid_corporate_event', None
    edge_case_guidance: str | None = None


class QueryDisambiguator:
    """Resolves ambiguity, documents assumptions, and handles financial edge cases (Day 10)."""

    def disambiguate(self, analysis: QueryAnalysis) -> DisambiguationResult:
        """Process a query analysis and produce structured disambiguation logic."""
        query_text = analysis.original_query
        lower = query_text.lower()

        reasons: list[str] = []
        questions: list[str] = []
        assumptions: list[str] = []
        focused_scope = ""
        edge_case = None
        guidance = None

        # Edge Case 1: Private Company detection
        private_entities = ["openai", "spacex", "stripe", "bytedance", "anthropic", "databricks"]
        if any(p in lower for p in private_entities):
            edge_case = "private_company"
            reasons.append("Subject is a private company with no mandatory public SEC filings (10-K/10-Q).")
            assumptions.append("Excluding SEC EDGAR statutory filings; relying on verified press releases, venture funding rounds, and executive disclosures.")
            guidance = "Flag all numerical valuations as estimated private-market valuations rather than audited figures."

        # Edge Case 2: Ambiguous thematic prompt (e.g. Challenge 6: 'What's happening with the banks?')
        elif "bank" in lower and analysis.ambiguity_level == "high":
            reasons.extend([
                "Target sub-sector is unspecified (e.g., Regional banks, Global Systemically Important Banks [G-SIBs], or Investment Banks).",
                "Geographic jurisdiction is unspecified (US Federal Reserve jurisdiction vs European ECB vs Asia-Pacific).",
                "Temporal catalyst is unspecified (Current interest-rate regime vs commercial real estate exposure vs regulatory stress tests).",
            ])
            questions.extend([
                "Would you like to focus on US regional banks (liquidity and CRE exposure) or Global Systemically Important Banks (JPMorgan, Citigroup, BofA)?",
                "Are you evaluating deposit flight trends, net interest margin (NIM) trajectory, or regulatory capital rules (Basel III endgame)?",
            ])
            assumptions.extend([
                "Assumption 1: Focus primarily on major US commercial and investment banks (JPMorgan Chase, Bank of America, Goldman Sachs).",
                "Assumption 2: Frame the analysis around macro monetary dynamics: Net Interest Margin (NIM) pressure, deposit migration, and Commercial Real Estate (CRE) credit provisions.",
                "Assumption 3: Examine regulatory compliance and capital adequacy metrics post-2023 regional banking turmoil.",
            ])
            focused_scope = "US Commercial & Regional Banking Sector: Net Interest Margins, Credit Quality, and Capital Adequacy"

        # Edge Case 3: Conglomerate / Multi-Division Ambiguity (e.g. Amazon: Retail vs AWS)
        elif "amazon" in lower and not any(w in lower for w in ("aws", "cloud", "retail")):
            reasons.append("Query is ambiguous between Amazon e-commerce retail, AWS cloud infrastructure, and advertising services.")
            questions.append("Do you want to focus on Amazon Web Services (AWS) margins or consolidated retail and logistics operations?")
            assumptions.append("Proceeding with consolidated corporate analysis with dedicated segment deep-dive into AWS.")
            focused_scope = "Consolidated Amazon.com Inc. with AWS Infrastructure Breakdown"

        # Edge Case 4: Rapid Corporate Event / Acquisition
        elif analysis.rate_of_change_detected:
            edge_case = "rapid_corporate_event"
            reasons.append("Company is actively undergoing a high-velocity corporate restructuring, acquisition, or legal action.")
            assumptions.append("Prioritize the most recent news wires and 8-K current event filings over older 10-K annual figures.")
            guidance = "Attach high temporal sensitivity alert to all valuation estimates."
            focused_scope = f"Event-driven impact analysis for {', '.join(analysis.target_tickers) or 'target'}"

        else:
            focused_scope = f"Standard financial equity research on {', '.join(analysis.target_tickers) or query_text}"

        is_ambiguous = len(reasons) > 0 or analysis.ambiguity_level in ("medium", "high")

        return DisambiguationResult(
            original_query=query_text,
            is_ambiguous=is_ambiguous,
            ambiguity_reasons=reasons,
            clarifying_questions=questions,
            documented_assumptions=assumptions,
            focused_scope=focused_scope,
            edge_case_type=edge_case,
            edge_case_guidance=guidance,
        )
