"""Vector database tools for the financial research agent."""

import logging
from typing import Any
from memory.vector_store import FinancialVectorStore

logger = logging.getLogger(__name__)

# Singleton vector store instance for tools
_vector_store: FinancialVectorStore | None = None


def get_shared_vector_store() -> FinancialVectorStore:
    """Get or initialize the shared financial vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FinancialVectorStore()
    return _vector_store


def vector_db_search(
    query: str,
    top_k: int = 5,
    ticker: str | None = None,
) -> dict[str, Any]:
    """Search the agent's long-term vector memory for previously stored research."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")

    store = get_shared_vector_store()
    if store.count() == 0:
        return {
            "query": query,
            "results": [],
            "count": 0,
            "message": "Long-term vector database is currently empty.",
        }

    records = store.search(query=query, n_results=top_k, ticker=ticker)

    formatted = []
    for r in records:
        formatted.append({
            "id": r["id"],
            "ticker": r["ticker"],
            "source_type": r["source_type"],
            "content": r["content"],
            "date": r["date"],
            "confidence": r["confidence"],
            "similarity_distance": r.get("distance"),
        })

    return {
        "query": query,
        "results": formatted,
        "count": len(formatted),
        "data_source": "chromadb_long_term_memory",
    }


def vector_db_store(
    content: str,
    ticker: str,
    source_type: str,
    confidence: float = 0.9,
) -> dict[str, Any]:
    """Store research findings into the agent's long-term vector memory."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("content must be a non-empty string")
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError("ticker must be a non-empty string")

    store = get_shared_vector_store()
    record_id = store.add_record(
        content=content.strip(),
        ticker=ticker.strip().upper(),
        source_type=source_type,
        date="2026-10-15T00:00:00Z",
        confidence=float(confidence),
        researcher_session="agent_session_active",
    )

    return {
        "status": "stored",
        "record_id": record_id,
        "ticker": ticker.strip().upper(),
        "source_type": source_type,
        "total_records_in_db": store.count(),
    }
