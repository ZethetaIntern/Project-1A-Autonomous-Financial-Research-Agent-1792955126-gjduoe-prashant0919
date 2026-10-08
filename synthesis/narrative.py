"""Narrative threading and sentiment-fact divergence detection for multi-source synthesis."""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NarrativeThread:
    """A coherent analytical thread weaving qualitative and quantitative evidence."""

    theme: str
    thesis: str
    quantitative_facts: list[str]
    qualitative_commentary: list[str]
    sources: list[str]
    synthesis_conclusion: str
    alignment_status: str  # 'aligned', 'divergent_positive_spin', 'divergent_unwarranted_pessimism'
    divergence_notes: str | None = None


class NarrativeSynthesizer:
    """Synthesizes narrative threads and checks sentiment-fact alignment (Section A6.4)."""

    def analyze_sentiment_fact_alignment(
        self,
        reported_growth_pct: float | None,
        operating_margin_trend: str,  # 'expanding', 'stable', 'contracting'
        qualitative_sentiment_score: float,  # -1.0 to +1.0
        management_tone: str = "neutral",
    ) -> dict[str, Any]:
        """Detect alignment or divergence between financial fundamentals and qualitative sentiment."""
        is_hard_numbers_strong = (
            (reported_growth_pct is not None and reported_growth_pct > 10.0)
            and operating_margin_trend in ("expanding", "stable")
        )
        is_hard_numbers_weak = (
            (reported_growth_pct is not None and reported_growth_pct < 0)
            or operating_margin_trend == "contracting"
        )

        alignment_status = "aligned"
        finding = ""

        # Divergence Case A: Positive sentiment/spin but deteriorating fundamentals
        if is_hard_numbers_weak and qualitative_sentiment_score > 0.3:
            alignment_status = "divergent_positive_spin"
            finding = (
                "Analytical Finding: Significant Divergence. Management commentary and news sentiment "
                "are optimistic, yet quantitative metrics indicate contracting margins or slowing revenue. "
                "Forward-looking estimates face execution risk."
            )
        # Divergence Case B: Highly negative news/sentiment despite strong fundamentals
        elif is_hard_numbers_strong and qualitative_sentiment_score < -0.2:
            alignment_status = "divergent_unwarranted_pessimism"
            finding = (
                "Analytical Finding: Sentiment Lag / Opportunity Divergence. Public media sentiment reflects "
                "pessimism or short-term noise, but underlying GAAP financial statements show double-digit "
                "revenue growth and operating discipline."
            )
        else:
            finding = (
                "Analytical Finding: High Coherence. Qualitative market sentiment closely tracks the "
                "reported quantitative performance of the company."
            )

        return {
            "alignment_status": alignment_status,
            "finding": finding,
            "sentiment_score": qualitative_sentiment_score,
            "margin_trend": operating_margin_trend,
            "growth_pct": reported_growth_pct,
        }

    def thread_narrative(
        self,
        company_name: str,
        theme: str,
        financial_findings: list[str],
        news_findings: list[str],
        management_quotes: list[str],
        sources: list[str],
    ) -> NarrativeThread:
        """Construct a unified narrative thread from multi-source evidence."""
        thesis = f"{company_name}'s strategic execution in {theme} is driving operational restructuring."

        conclusions = []
        if financial_findings:
            conclusions.append(f"Financial disclosures demonstrate that {financial_findings[0].lower()}")
        if management_quotes:
            conclusions.append(f"Management commentary emphasizes that {management_quotes[0].lower()}")
        if news_findings:
            conclusions.append(f"External market reports corroborate that {news_findings[0].lower()}")

        full_synthesis = " Furthermore, ".join(conclusions) if conclusions else "Comprehensive synthesis ongoing."

        return NarrativeThread(
            theme=theme,
            thesis=thesis,
            quantitative_facts=financial_findings,
            qualitative_commentary=news_findings + management_quotes,
            sources=sources,
            synthesis_conclusion=full_synthesis,
            alignment_status="aligned",
        )
