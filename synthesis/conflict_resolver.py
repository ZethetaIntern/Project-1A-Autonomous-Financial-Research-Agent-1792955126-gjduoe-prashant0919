"""Multi-source conflict resolution protocol for financial research data."""

import logging
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

logger = logging.getLogger(__name__)


class ReliabilityTier(IntEnum):
    """Source reliability tier hierarchy according to Section A6.2 (Corrected)."""

    TIER_1_SEC_FILINGS = 1          # 10-K (audited), 10-Q (reviewed), 8-K
    TIER_2_FINANCIAL_APIS = 2       # Bloomberg, FactSet, Refinitiv, S&P, yfinance
    TIER_3_EARNINGS_TRANSCRIPTS = 3 # Earnings call transcripts, management Q&A
    TIER_4_MAJOR_NEWS = 4           # Reuters, Bloomberg News, FT, WSJ
    TIER_5_UNVERIFIED_SOCIAL = 5    # Anonymous forums, unverified social media


@dataclass
class SourceDataPoint:
    """A data point tagged with source identity, tier, timestamp, and period."""

    metric: str
    value: Any
    source_name: str
    source_tier: ReliabilityTier
    period: str | None = None          # e.g., 'Q3 2026', 'FY2025'
    timestamp: str | None = None
    is_restated: bool = False
    confidence: float = 1.0


@dataclass
class ConflictResolution:
    """The result of resolving a conflict between disparate source observations."""

    metric: str
    has_conflict: bool
    resolved_value: Any
    resolution_method: str             # e.g., 'temporal_difference', 'restatement_override', 'highest_tier_rule', 'triangulated_consensus'
    chosen_source: str
    confidence: float
    explanation: str
    conflicting_sources: list[dict[str, Any]] = field(default_factory=list)


class ConflictResolver:
    """Executes the systematic 6-step conflict resolution protocol (Section A6.3)."""

    def __init__(self, tolerance_pct: float = 5.0) -> None:
        self.tolerance_pct = tolerance_pct

    def classify_source_tier(self, source_name: str) -> ReliabilityTier:
        """Classify a source into its canonical trustworthiness tier."""
        name_lower = source_name.lower()

        if any(k in name_lower for k in ("10-k", "10-q", "8-k", "edgar", "sec")):
            return ReliabilityTier.TIER_1_SEC_FILINGS
        if any(k in name_lower for k in ("bloomberg terminal", "factset", "refinitiv", "yfinance", "financial_api", "balance_sheet")):
            return ReliabilityTier.TIER_2_FINANCIAL_APIS
        if any(k in name_lower for k in ("transcript", "earnings_call", "prepared remarks", "q&a")):
            return ReliabilityTier.TIER_3_EARNINGS_TRANSCRIPTS
        if any(k in name_lower for k in ("reuters", "bloomberg news", "financial times", "wsj", "wall street journal", "news")):
            return ReliabilityTier.TIER_4_MAJOR_NEWS
        return ReliabilityTier.TIER_5_UNVERIFIED_SOCIAL

    def resolve(
        self,
        metric: str,
        data_points: list[SourceDataPoint],
    ) -> ConflictResolution:
        """Apply the 6-step resolution protocol to conflicting data points."""
        if not data_points:
            raise ValueError("Must provide at least one data point to resolve")

        if len(data_points) == 1:
            dp = data_points[0]
            return ConflictResolution(
                metric=metric,
                has_conflict=False,
                resolved_value=dp.value,
                resolution_method="single_source",
                chosen_source=dp.source_name,
                confidence=dp.confidence,
                explanation=f"Single source available from {dp.source_name}.",
                conflicting_sources=[{
                    "source": dp.source_name,
                    "value": dp.value,
                    "tier": dp.source_tier.name,
                }],
            )

        # Step 1: Identify the conflict
        # Compare numeric values or distinct categorical strings
        values = [dp.value for dp in data_points]
        all_numeric = all(isinstance(v, (int, float)) for v in values)

        conflict_detected = False
        if all_numeric:
            min_val = min(values)
            max_val = max(values)
            if min_val > 0:
                spread_pct = ((max_val - min_val) / min_val) * 100
                if spread_pct > self.tolerance_pct:
                    conflict_detected = True
            elif min_val != max_val:
                conflict_detected = True
        else:
            if len(set(str(v).strip().lower() for v in values)) > 1:
                conflict_detected = True

        if not conflict_detected:
            # Sources agree within tolerance
            best_tier_dp = min(data_points, key=lambda dp: dp.source_tier.value)
            return ConflictResolution(
                metric=metric,
                has_conflict=False,
                resolved_value=best_tier_dp.value,
                resolution_method="consensus_agreement",
                chosen_source=best_tier_dp.source_name,
                confidence=0.98,
                explanation=f"All {len(data_points)} sources agree within {self.tolerance_pct}% tolerance.",
                conflicting_sources=[{"source": dp.source_name, "value": dp.value, "tier": dp.source_tier.name} for dp in data_points],
            )

        # Step 3: Check for temporal differences
        periods = set(dp.period for dp in data_points if dp.period)
        if len(periods) > 1:
            # Different periods: sort by newest period / timestamp
            sorted_by_recency = sorted(data_points, key=lambda dp: (dp.period or "", dp.timestamp or ""), reverse=True)
            chosen = sorted_by_recency[0]
            return ConflictResolution(
                metric=metric,
                has_conflict=True,
                resolved_value=chosen.value,
                resolution_method="temporal_difference",
                chosen_source=chosen.source_name,
                confidence=0.92,
                explanation=(
                    f"Discrepancy explained by temporal difference across periods ({', '.join(periods)}). "
                    f"Selected most recent period '{chosen.period}' from {chosen.source_name}."
                ),
                conflicting_sources=[{"source": dp.source_name, "value": dp.value, "period": dp.period} for dp in data_points],
            )

        # Step 4: Look for restatements
        restated_points = [dp for dp in data_points if dp.is_restated]
        if restated_points:
            chosen = restated_points[0]
            return ConflictResolution(
                metric=metric,
                has_conflict=True,
                resolved_value=chosen.value,
                resolution_method="restatement_override",
                chosen_source=chosen.source_name,
                confidence=0.95,
                explanation=f"Company restated historical financials. Adopted restated figure from {chosen.source_name}.",
                conflicting_sources=[{"source": dp.source_name, "value": dp.value, "is_restated": dp.is_restated} for dp in data_points],
            )

        # Step 5: Apply highest-tier rule
        # Sort by tier (lowest integer = highest trustworthiness)
        sorted_by_tier = sorted(data_points, key=lambda dp: (dp.source_tier.value, -dp.confidence))
        chosen = sorted_by_tier[0]
        other_tiers = [f"{dp.source_name} ({dp.source_tier.name}: {dp.value})" for dp in sorted_by_tier[1:]]

        return ConflictResolution(
            metric=metric,
            has_conflict=True,
            resolved_value=chosen.value,
            resolution_method="highest_tier_rule",
            chosen_source=chosen.source_name,
            confidence=0.90,
            explanation=(
                f"Resolved via Highest-Tier Rule. Selected {chosen.source_tier.name} from {chosen.source_name} "
                f"({chosen.value}) over lower tier sources: {'; '.join(other_tiers)}."
            ),
            conflicting_sources=[{"source": dp.source_name, "value": dp.value, "tier": dp.source_tier.name} for dp in data_points],
        )
