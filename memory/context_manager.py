"""Short-term memory management and context budgeting for financial research."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ContextChunk:
    """A tagged piece of research evidence managed within short-term memory."""

    content: str
    source_type: str  # e.g., '10-K', 'financial_data', 'news', 'earnings_transcript'
    source_title: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    confidence: float = 1.0
    tokens_estimate: int = 0
    priority: int = 1  # 1 = highest, 5 = lowest

    def __post_init__(self) -> None:
        if not self.tokens_estimate:
            # Approximate 4 characters per token
            self.tokens_estimate = max(1, len(self.content) // 4)


class ContextManager:
    """Manages short-term working memory, token budgets, and context window limits."""

    # Default token budget allocations (Section A8.2 Stage 4)
    # 40% primary data (filings, financials)
    # 30% supporting evidence (news, transcripts, web)
    # 20% system prompt and tool definitions
    # 10% generation space
    PRIMARY_BUDGET_RATIO = 0.40
    SUPPORTING_BUDGET_RATIO = 0.30
    PROMPT_BUDGET_RATIO = 0.20
    GENERATION_BUDGET_RATIO = 0.10

    def __init__(self, max_context_tokens: int = 8000) -> None:
        if max_context_tokens < 500:
            raise ValueError("max_context_tokens must be at least 500")

        self.max_context_tokens = max_context_tokens
        self.primary_budget = int(max_context_tokens * self.PRIMARY_BUDGET_RATIO)
        self.supporting_budget = int(
            max_context_tokens * self.SUPPORTING_BUDGET_RATIO
        )
        self.prompt_budget = int(max_context_tokens * self.PROMPT_BUDGET_RATIO)
        self.generation_budget = int(
            max_context_tokens * self.GENERATION_BUDGET_RATIO
        )

        self.primary_chunks: list[ContextChunk] = []
        self.supporting_chunks: list[ContextChunk] = []
        self.summaries: list[str] = []

    def is_primary_source(self, source_type: str) -> bool:
        """Determine whether a source type is classified as primary data."""
        primary_types = {
            "10-k",
            "10-q",
            "8-k",
            "sec_filing",
            "financial_data",
            "balance_sheet",
            "income_statement",
            "cash_flow",
        }
        return source_type.lower() in primary_types

    def add_chunk(
        self,
        content: str,
        source_type: str,
        source_title: str,
        confidence: float = 1.0,
        timestamp: str | None = None,
        priority: int = 1,
    ) -> ContextChunk:
        """Add a chunk of evidence to the appropriate memory partition."""
        chunk = ContextChunk(
            content=content,
            source_type=source_type,
            source_title=source_title,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            confidence=confidence,
            priority=priority,
        )

        if self.is_primary_source(source_type):
            self.primary_chunks.append(chunk)
            self._prune_partition(self.primary_chunks, self.primary_budget)
        else:
            self.supporting_chunks.append(chunk)
            self._prune_partition(
                self.supporting_chunks, self.supporting_budget
            )

        logger.debug(
            "Added chunk from %s (%s tokens) to context",
            source_type,
            chunk.tokens_estimate,
        )
        return chunk

    def _prune_partition(
        self, chunks: list[ContextChunk], budget_tokens: int
    ) -> None:
        """Prune chunks in a partition if they exceed token budget using recency and priority."""
        total_tokens = sum(c.tokens_estimate for c in chunks)
        if total_tokens <= budget_tokens:
            return

        # Sort chunks: keep higher priority (lower int) and more recent timestamps
        chunks.sort(key=lambda c: (c.priority, -c.confidence))

        # Evict lowest-ranked items until within budget, compressing evicted into summaries
        evicted = []
        while chunks and sum(c.tokens_estimate for c in chunks) > budget_tokens:
            evicted.append(chunks.pop())

        if evicted:
            summary = self._summarize_evicted(evicted)
            if summary:
                self.summaries.append(summary)

    def _summarize_evicted(self, evicted_chunks: list[ContextChunk]) -> str:
        """Progressively summarize evicted context items to preserve historical facts."""
        key_points = []
        for c in evicted_chunks:
            snippet = c.content.strip().split("\n")[0][:120]
            key_points.append(f"[{c.source_type} - {c.source_title}] {snippet}")
        return "Condensed historical context:\n- " + "\n- ".join(key_points)

    def assemble_context(self) -> str:
        """Assemble current working context respecting diversity, recency, and budgeting."""
        sections = []

        if self.summaries:
            sections.append("### Previous Research Synthesis")
            sections.append("\n".join(self.summaries[-3:]))

        if self.primary_chunks:
            sections.append("### Primary Regulatory & Financial Data")
            # Recency weighting: newest first
            sorted_primary = sorted(
                self.primary_chunks, key=lambda c: c.timestamp, reverse=True
            )
            for chunk in sorted_primary:
                sections.append(
                    f"**Source:** {chunk.source_title} ({chunk.source_type}) | Date: {chunk.timestamp} | Confidence: {chunk.confidence:.2f}\n"
                    f"{chunk.content}\n"
                )

        if self.supporting_chunks:
            sections.append("### Supporting Intelligence & Market Commentary")
            sorted_supporting = sorted(
                self.supporting_chunks, key=lambda c: c.timestamp, reverse=True
            )
            for chunk in sorted_supporting:
                sections.append(
                    f"**Source:** {chunk.source_title} ({chunk.source_type}) | Date: {chunk.timestamp} | Confidence: {chunk.confidence:.2f}\n"
                    f"{chunk.content}\n"
                )

        return "\n\n".join(sections)

    def get_token_usage_stats(self) -> dict[str, Any]:
        """Return token utilization metrics across all memory partitions."""
        primary_tokens = sum(c.tokens_estimate for c in self.primary_chunks)
        supporting_tokens = sum(
            c.tokens_estimate for c in self.supporting_chunks
        )
        summary_tokens = sum(len(s) // 4 for s in self.summaries)
        total_used = primary_tokens + supporting_tokens + summary_tokens

        return {
            "total_tokens_used": total_used,
            "max_context_tokens": self.max_context_tokens,
            "utilization_pct": round(
                (total_used / self.max_context_tokens) * 100, 2
            ),
            "primary_tokens": primary_tokens,
            "primary_budget": self.primary_budget,
            "supporting_tokens": supporting_tokens,
            "supporting_budget": self.supporting_budget,
            "summaries_count": len(self.summaries),
        }

    def clear(self) -> None:
        """Clear all working memory partitions."""
        self.primary_chunks.clear()
        self.supporting_chunks.clear()
        self.summaries.clear()
