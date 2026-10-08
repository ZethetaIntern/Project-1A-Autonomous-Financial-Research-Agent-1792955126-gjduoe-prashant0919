"""Tests for the multi-source synthesis engine, conflict resolver, and narrative threading."""

import pytest
from synthesis.conflict_resolver import ConflictResolver, ReliabilityTier, SourceDataPoint
from synthesis.narrative import NarrativeSynthesizer
from synthesis.engine import MultiSourceSynthesisEngine


@pytest.fixture
def resolver():
    return ConflictResolver(tolerance_pct=5.0)


@pytest.fixture
def narrative():
    return NarrativeSynthesizer()


@pytest.fixture
def engine():
    return MultiSourceSynthesisEngine()


def test_conflict_resolver_tier_classification(resolver):
    assert resolver.classify_source_tier("Microsoft 10-K Filing") == ReliabilityTier.TIER_1_SEC_FILINGS
    assert resolver.classify_source_tier("Bloomberg Terminal Data API") == ReliabilityTier.TIER_2_FINANCIAL_APIS
    assert resolver.classify_source_tier("Q3 2026 Earnings Call Transcript") == ReliabilityTier.TIER_3_EARNINGS_TRANSCRIPTS
    assert resolver.classify_source_tier("Reuters Market Wire") == ReliabilityTier.TIER_4_MAJOR_NEWS
    assert resolver.classify_source_tier("Reddit WallStreetBets Discussion") == ReliabilityTier.TIER_5_UNVERIFIED_SOCIAL


def test_conflict_resolver_highest_tier_rule(resolver):
    pts = [
        SourceDataPoint(
            metric="Revenue",
            value=100.0,
            source_name="SEC 10-K",
            source_tier=ReliabilityTier.TIER_1_SEC_FILINGS,
        ),
        SourceDataPoint(
            metric="Revenue",
            value=85.0,
            source_name="TechBlog Forum",
            source_tier=ReliabilityTier.TIER_5_UNVERIFIED_SOCIAL,
        ),
    ]

    res = resolver.resolve("Revenue", pts)
    assert res.has_conflict is True
    assert res.resolved_value == 100.0
    assert res.resolution_method == "highest_tier_rule"
    assert res.chosen_source == "SEC 10-K"


def test_conflict_resolver_temporal_difference(resolver):
    pts = [
        SourceDataPoint(
            metric="Cash",
            value=25.0,
            source_name="Q2 Form 10-Q",
            source_tier=ReliabilityTier.TIER_1_SEC_FILINGS,
            period="Q2 2026",
            timestamp="2026-06-30",
        ),
        SourceDataPoint(
            metric="Cash",
            value=32.0,
            source_name="Q3 Form 10-Q",
            source_tier=ReliabilityTier.TIER_1_SEC_FILINGS,
            period="Q3 2026",
            timestamp="2026-09-30",
        ),
    ]

    res = resolver.resolve("Cash", pts)
    assert res.has_conflict is True
    assert res.resolution_method == "temporal_difference"
    assert res.resolved_value == 32.0
    assert "Q3" in res.explanation


def test_conflict_resolver_restatement(resolver):
    pts = [
        SourceDataPoint(
            metric="Operating Margin",
            value=0.18,
            source_name="Original 2024 Filing",
            source_tier=ReliabilityTier.TIER_1_SEC_FILINGS,
            is_restated=False,
        ),
        SourceDataPoint(
            metric="Operating Margin",
            value=0.14,
            source_name="2025 10-K Restatement Note",
            source_tier=ReliabilityTier.TIER_1_SEC_FILINGS,
            is_restated=True,
        ),
    ]

    res = resolver.resolve("Operating Margin", pts)
    assert res.has_conflict is True
    assert res.resolution_method == "restatement_override"
    assert res.resolved_value == 0.14


def test_sentiment_fact_divergence(narrative):
    # Case: Positive executive commentary, but negative fundamentals
    result = narrative.analyze_sentiment_fact_alignment(
        reported_growth_pct=-5.0,
        operating_margin_trend="contracting",
        qualitative_sentiment_score=0.75,
    )
    assert result["alignment_status"] == "divergent_positive_spin"
    assert "Divergence" in result["finding"]

    # Case: Strong fundamentals, but negative market chatter (e.g. Palantir challenge)
    pltr_res = narrative.analyze_sentiment_fact_alignment(
        reported_growth_pct=27.0,
        operating_margin_trend="expanding",
        qualitative_sentiment_score=-0.40,
    )
    assert pltr_res["alignment_status"] == "divergent_unwarranted_pessimism"


def test_quantitative_triangulation(engine):
    # 3 sources where 2 agree
    obs = [
        {"source": "SEC 10-K", "value": 100.0, "tier": ReliabilityTier.TIER_1_SEC_FILINGS},
        {"source": "Bloomberg API", "value": 100.5, "tier": ReliabilityTier.TIER_2_FINANCIAL_APIS},
        {"source": "News Snippet", "value": 75.0, "tier": ReliabilityTier.TIER_4_MAJOR_NEWS},
    ]

    triangulated = engine.triangulate_numerical_metric("Revenue", obs)
    assert triangulated["status"] == "triangulated_consensus"
    assert triangulated["confidence"] >= 0.90
    assert 100.0 <= triangulated["consensus_value"] <= 100.5

    # 3 sources all disagree
    disagree_obs = [
        {"source": "SEC 10-K", "value": 100.0, "tier": ReliabilityTier.TIER_1_SEC_FILINGS},
        {"source": "Bloomberg API", "value": 140.0, "tier": ReliabilityTier.TIER_2_FINANCIAL_APIS},
        {"source": "News Snippet", "value": 60.0, "tier": ReliabilityTier.TIER_4_MAJOR_NEWS},
    ]
    disagree_res = engine.triangulate_numerical_metric("Revenue", disagree_obs)
    assert disagree_res["status"] == "discrepancy_range_reported"
    assert disagree_res["range"] == [60.0, 140.0]
    assert disagree_res["recommended_value"] == 100.0
