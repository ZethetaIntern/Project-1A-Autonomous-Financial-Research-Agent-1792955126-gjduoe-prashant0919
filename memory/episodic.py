"""Episodic memory recording research strategies, query types, and process experience."""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

EPISODIC_FILE_DEFAULT = Path(__file__).resolve().parent.parent / "data" / "episodic_memory.json"


@dataclass
class Episode:
    """A recorded research episode capturing query context, tool path, and outcomes."""

    session_id: str
    query: str
    query_type: str  # e.g., 'company_profile', 'earnings_analysis', 'risk_assessment', 'industry_comparison'
    ticker: str
    tools_used: list[str]
    success: bool
    iterations: int
    duration_seconds: float
    key_findings_count: int
    strategy_notes: str
    errors_encountered: list[str] = field(default_factory=list)
    recovery_strategies: list[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EpisodicMemory:
    """Persists and retrieves episodic execution memories to guide future planning."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.storage_path = Path(storage_path or EPISODIC_FILE_DEFAULT)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.episodes: list[Episode] = []
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self.episodes = [Episode(**item) for item in data]
                logger.info("Loaded %d episodes from %s", len(self.episodes), self.storage_path)
            except Exception as exc:
                logger.warning("Failed to load episodic memory: %s", exc)
                self.episodes = []

    def save(self) -> None:
        try:
            raw = [asdict(e) for e in self.episodes]
            self.storage_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.error("Failed to save episodic memory: %s", exc)

    def record_episode(self, episode: Episode) -> None:
        """Add and persist a new episode."""
        self.episodes.append(episode)
        self.save()
        logger.info(
            "Recorded episode for %s (%s, success=%s)",
            episode.ticker,
            episode.query_type,
            episode.success,
        )

    def get_strategy_recommendation(self, query_type: str, ticker: str | None = None) -> dict[str, Any]:
        """Recommend optimal tool sequence and precautions based on historical episodes."""
        matching = [e for e in self.episodes if e.query_type.lower() == query_type.lower()]
        if not matching:
            # Fallback to general successful episodes
            matching = [e for e in self.episodes if e.success]

        if not matching:
            return {
                "recommended_tools": [],
                "confidence": 0.0,
                "known_pitfalls": [],
                "prior_episodes_analyzed": 0,
            }

        # Count tool frequencies among successful episodes
        tool_counts: dict[str, int] = {}
        pitfalls: list[str] = []
        recoveries: list[str] = []

        for ep in matching:
            if ep.success:
                for tool in ep.tools_used:
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1
            if ep.errors_encountered:
                pitfalls.extend(ep.errors_encountered)
            if ep.recovery_strategies:
                recoveries.extend(ep.recovery_strategies)

        sorted_tools = sorted(tool_counts.keys(), key=lambda t: tool_counts[t], reverse=True)

        return {
            "query_type": query_type,
            "recommended_tools": sorted_tools[:5],
            "confidence": round(min(1.0, len(matching) * 0.25), 2),
            "known_pitfalls": list(set(pitfalls))[:5],
            "recommended_recoveries": list(set(recoveries))[:5],
            "prior_episodes_analyzed": len(matching),
        }

    def get_all_episodes(self) -> list[Episode]:
        """Return all recorded episodes."""
        return list(self.episodes)

    def clear(self) -> None:
        """Clear memory."""
        self.episodes.clear()
        if self.storage_path.exists():
            self.storage_path.unlink()
