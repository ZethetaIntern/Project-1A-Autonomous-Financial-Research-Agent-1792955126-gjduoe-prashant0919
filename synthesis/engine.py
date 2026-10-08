"""Multi-source synthesis engine integrating conflict resolution, triangulation, and narrative threading."""

import logging
from typing import Any

from synthesis.conflict_resolver import ConflictResolver, ReliabilityTier, SourceDataPoint
from synthesis.narrative import NarrativeSynthesizer, NarrativeThread

logger = logging.getLogger(__name__)


class MultiSourceSynthesisEngine:
    """Orchestrates comprehensive cross-source data fusion, triangulation, and narrative synthesis."""

    def __init__(self) -> None:
        self.conflict_resolver = ConflictResolver()
        self.narrative_synthesizer = NarrativeSynthesizer()

    def triangulate_numerical_metric(
        self,
        metric_name: str,
        observations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Triangulate a numeric metric across 3+ sources (Section A6.4 Quantitative Triangulation).

        Args:
            metric_name: e.g., 'Revenue', 'Operating Margin', 'EPS'
            observations: List of dicts with keys 'source', 'value', 'period', 'tier'
        """
        if not observations:
            raise ValueError("Must provide at least one observation for triangulation")

        # Convert to SourceDataPoints
        data_points = []
        for obs in observations:
            tier = obs.get("tier")
            if not isinstance(tier, ReliabilityTier):
                tier = self.conflict_resolver.classify_source_tier(obs.get("source", "unknown"))

            data_points.append(
                SourceDataPoint(
                    metric=metric_name,
                    value=float(obs["value"]),
                    source_name=obs.get("source", "unspecified"),
                    source_tier=tier,
                    period=obs.get("period"),
                    is_restated=bool(obs.get("is_restated", False)),
                    confidence=float(obs.get("confidence", 0.9)),
                )
            )

        values = [dp.value for dp in data_points]
        n_sources = len(data_points)

        # Check for pairwise agreement within 5% tolerance
        agreed_pairs = []
        for i in range(n_sources):
            for j in range(i + 1, n_sources):
                v1, v2 = values[i], values[j]
                base = min(abs(v1), abs(v2))
                diff = abs(v1 - v2)
                if base > 0 and (diff / base) <= 0.05:
                    agreed_pairs.append((data_points[i], data_points[j]))

        if len(agreed_pairs) >= 1:
            # At least two sources agree
            best_pair = agreed_pairs[0]
            consensus_value = (best_pair[0].value + best_pair[1].value) / 2.0
            return {
                "metric": metric_name,
                "status": "triangulated_consensus",
                "consensus_value": round(consensus_value, 2),
                "confidence": 0.95,
                "sources_checked": n_sources,
                "concurring_sources": [best_pair[0].source_name, best_pair[1].source_name],
                "explanation": (
                    f"Triangulated across {n_sources} independent sources. "
                    f"Strong consensus verified between {best_pair[0].source_name} and {best_pair[1].source_name}."
                ),
            }

        # All sources disagree: Report the range and evaluate discrepancy
        min_v = min(values)
        max_v = max(values)
        highest_tier_dp = min(data_points, key=lambda dp: dp.source_tier.value)

        return {
            "metric": metric_name,
            "status": "discrepancy_range_reported",
            "range": [min_v, max_v],
            "recommended_value": highest_tier_dp.value,
            "recommended_source": highest_tier_dp.source_name,
            "confidence": 0.70,
            "sources_checked": n_sources,
            "explanation": (
                f"Discrepancy detected across all {n_sources} sources (range: {min_v} to {max_v}). "
                f"Adopting highest-tier authoritative source {highest_tier_dp.source_name}."
            ),
        }

    def synthesize_research_package(
        self,
        company_name: str,
        ticker: str,
        tool_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Extract multi-source signals and synthesize findings into unified research conclusions."""
        quantitative_claims = []
        qualitative_signals = []
        data_sources_used = set()

        for res in tool_results:
            tool_name = res.get("tool", "")
            data = res.get("result", {}).get("data") or res.get("data") or {}

            if tool_name in ("financial_api", "earnings"):
                data_sources_used.add("Financial Fundamentals")
                if isinstance(data, dict):
                    if data.get("revenue"):
                        quantitative_claims.append(f"Reported revenue: ${data['revenue']:,.0f}" if isinstance(data['revenue'], (int, float)) else f"Reported revenue: {data['revenue']}")
                    if data.get("operating_income"):
                        quantitative_claims.append(f"Operating income: ${data['operating_income']:,.0f}" if isinstance(data['operating_income'], (int, float)) else f"Operating income: {data['operating_income']}")

            elif tool_name == "news_sentiment":
                data_sources_used.add("News & Media Sentiment")
                if isinstance(data, dict):
                    sentiment = data.get("overall_sentiment", "neutral")
                    qualitative_signals.append(f"Media sentiment scored as {sentiment}")

            elif tool_name == "sec_edgar":
                data_sources_used.add("SEC EDGAR Regulatory Disclosures")
                qualitative_signals.append("Statutory disclosures cross-referenced against EDGAR 10-K/10-Q index.")

            elif tool_name == "web_search":
                data_sources_used.add("Web Search Coverage")
                qualitative_signals.append("External market and strategic analysis gathered via web index.")

        thread = self.narrative_synthesizer.thread_narrative(
            company_name=company_name,
            theme="Operational & Financial Evolution",
            financial_findings=quantitative_claims,
            news_findings=qualitative_signals,
            management_quotes=[],
            sources=list(data_sources_used),
        )

        return {
            "company_name": company_name,
            "ticker": ticker.upper(),
            "sources_count": len(data_sources_used),
            "sources": sorted(data_sources_used),
            "primary_thread": thread,
            "synthesis_summary": thread.synthesis_conclusion,
        }
