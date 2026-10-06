"""Comprehensive tests for three-layer memory system (vector store, context manager, episodic memory)."""

import tempfile
import pytest
from pathlib import Path

from memory.vector_store import FinancialVectorStore
from memory.context_manager import ContextManager
from memory.episodic import EpisodicMemory, Episode
from tools.vector_db_tools import vector_db_search, vector_db_store, get_shared_vector_store


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def test_vector_store_add_and_search(temp_dir):
    store = FinancialVectorStore(persist_directory=temp_dir)
    doc_id = store.add_record(
        content="Microsoft Azure cloud revenue increased 29% YoY in Q4.",
        ticker="MSFT",
        source_type="10-K",
        date="2026-07-30T00:00:00Z",
        confidence=0.95,
        researcher_session="test_session_1",
    )
    assert doc_id is not None
    assert store.count() == 1

    results = store.search(query="Azure cloud revenue", ticker="MSFT")
    assert len(results) == 1
    assert "Azure cloud revenue" in results[0]["content"]
    assert results[0]["ticker"] == "MSFT"


def test_context_manager_budgeting():
    cm = ContextManager(max_context_tokens=1000)
    assert cm.primary_budget == 400
    assert cm.supporting_budget == 300
    assert cm.prompt_budget == 200
    assert cm.generation_budget == 100

    # Add primary chunk
    cm.add_chunk(
        content="SEC 10-K filing excerpt: Net income was $88B.",
        source_type="10-K",
        source_title="Microsoft FY2026 10-K",
        confidence=0.99,
    )
    # Add supporting chunk
    cm.add_chunk(
        content="Reuters: Tech stocks rally led by enterprise cloud demand.",
        source_type="news",
        source_title="Reuters Market Report",
        confidence=0.85,
    )

    stats = cm.get_token_usage_stats()
    assert stats["total_tokens_used"] > 0
    assert stats["primary_tokens"] > 0
    assert stats["supporting_tokens"] > 0

    assembled = cm.assemble_context()
    assert "Primary Regulatory & Financial Data" in assembled
    assert "Supporting Intelligence & Market Commentary" in assembled


def test_context_manager_pruning_and_summarization():
    cm = ContextManager(max_context_tokens=600)  # Primary budget = 240 tokens (~960 chars)
    # Add large chunks exceeding budget to trigger pruning
    large_text = "Detailed financial balance sheet disclosure line item data. " * 30
    for i in range(5):
        cm.add_chunk(
            content=f"Chunk {i}: {large_text}",
            source_type="10-K",
            source_title=f"Filing Note {i}",
            priority=i + 1,
        )

    # Evicted items should be condensed into summaries
    assert len(cm.summaries) > 0
    assembled = cm.assemble_context()
    assert "Previous Research Synthesis" in assembled or "Primary Regulatory" in assembled


def test_episodic_memory(temp_dir):
    storage_path = temp_dir / "episodic.json"
    mem = EpisodicMemory(storage_path=storage_path)

    ep = Episode(
        session_id="session_101",
        query="Analyze Apple quarterly earnings",
        query_type="earnings_analysis",
        ticker="AAPL",
        tools_used=["financial_api", "earnings", "news_sentiment"],
        success=True,
        iterations=3,
        duration_seconds=12.4,
        key_findings_count=6,
        strategy_notes="Prioritizing financial_api first provided accurate consensus figures.",
    )
    mem.record_episode(ep)
    assert len(mem.get_all_episodes()) == 1

    recommendation = mem.get_strategy_recommendation("earnings_analysis")
    assert "financial_api" in recommendation["recommended_tools"]
    assert recommendation["prior_episodes_analyzed"] == 1


def test_vector_db_tools():
    store_result = vector_db_store(
        content="Tesla automotive gross margin contracted to 14.6% amid global price reductions.",
        ticker="TSLA",
        source_type="10-Q",
        confidence=0.92,
    )
    assert store_result["status"] == "stored"

    search_result = vector_db_search(query="Tesla automotive gross margin", ticker="TSLA")
    assert search_result["count"] >= 1
    assert any("gross margin" in r["content"] for r in search_result["results"])
