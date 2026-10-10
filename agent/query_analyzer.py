"""Query analyzer assessing query intent, entity extraction, complexity, and ambiguity."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QueryType(str, Enum):
    """Supported financial research query archetypes."""

    COMPANY_PROFILE = "company_profile"
    EARNINGS_ANALYSIS = "earnings_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    INDUSTRY_COMPARISON = "industry_comparison"
    CONTRADICTORY_DATA = "contradictory_data"
    AMBIGUOUS_THEMATIC = "ambiguous_thematic"
    SECTOR_MEMORY = "sector_memory"
    FULL_REPORT_DEGRADATION = "full_report_degradation"
    UNKNOWN = "unknown"


@dataclass
class QueryAnalysis:
    """The structured classification result of an incoming research query."""

    original_query: str
    query_type: QueryType
    complexity_score: int              # 1 (basic) to 5 (advanced synthesis)
    ambiguity_level: str               # 'low', 'medium', 'high'
    target_tickers: list[str] = field(default_factory=list)
    temporal_scope: str | None = None  # e.g., 'recent', 'historical', 'quarterly'
    is_multi_company: bool = False
    requires_memory: bool = False
    rate_of_change_detected: bool = False
    recommended_tools: list[str] = field(default_factory=list)


class QueryAnalyzer:
    """Analyzes and classifies incoming financial research prompts (Day 10)."""

    COMMON_TICKERS = {
        "MICROSOFT": "MSFT", "MSFT": "MSFT",
        "APPLE": "AAPL", "AAPL": "AAPL",
        "TESLA": "TSLA", "TSLA": "TSLA",
        "AMAZON": "AMZN", "AMZN": "AMZN",
        "GOOGLE": "GOOGL", "ALPHABET": "GOOGL", "GOOGL": "GOOGL",
        "NVIDIA": "NVDA", "NVDA": "NVDA",
        "PALANTIR": "PLTR", "PLTR": "PLTR",
        "JPMORGAN": "JPM", "JPM": "JPM",
        "GOLDMAN": "GS", "GS": "GS",
        "MORGAN STANLEY": "MS", "MS": "MS",
    }

    RAPID_CHANGE_MARKERS = [
        "acquisition", "merger", "restructuring", "hostile takeover",
        "investigation", "subpoena", "default", "bankruptcy", "short squeeze",
        "sudden departure", "breaking", "crisis",
    ]

    def analyze(self, query: str) -> QueryAnalysis:
        """Classify query intent, complexity, ambiguity, and entities."""
        text = query.strip()
        lower = text.lower()

        # 1. Entity and Ticker Extraction
        tickers: list[str] = []
        for name, ticker in self.COMMON_TICKERS.items():
            pattern = rf"\b{re.escape(name.lower())}\b"
            if re.search(pattern, lower) and ticker not in tickers:
                tickers.append(ticker)

        # Also regex for capital standalone symbols (e.g. MSFT, AAPL)
        raw_symbols = re.findall(r"\b[A-Z]{2,5}\b", text)
        for s in raw_symbols:
            if s in self.COMMON_TICKERS.values() and s not in tickers:
                tickers.append(s)

        is_multi = len(tickers) > 1

        # 2. Rate-of-Change Detection
        rate_of_change = any(marker in lower for marker in self.RAPID_CHANGE_MARKERS)

        # 3. Query Type and Complexity Scoring
        if any(w in lower for w in ("degradation", "failure rate", "simulate 50%", "intermittent")):
            qtype = QueryType.FULL_REPORT_DEGRADATION
            complexity = 5
            ambiguity = "low"
            tools = ["company_profile", "sec_edgar", "financial_api", "earnings", "web_search", "news_sentiment", "calculation_engine", "report_generator"]
            req_memory = True

        elif any(w in lower for w in ("sector", "cross-cutting", "themes emerge", "already researched")):
            qtype = QueryType.SECTOR_MEMORY
            complexity = 4
            ambiguity = "medium"
            tools = ["vector_db_search", "web_search", "report_generator"]
            req_memory = True

        elif any(w in lower for w in ("what's happening with", "what is happening with", "banks", "broadly")):
            qtype = QueryType.AMBIGUOUS_THEMATIC
            complexity = 4
            ambiguity = "high"
            tools = ["web_search", "news_sentiment", "financial_api", "report_generator"]
            req_memory = False

        elif any(w in lower for w in ("contradiction", "struggling", "apparent contradiction", "conflicting")):
            qtype = QueryType.CONTRADICTORY_DATA
            complexity = 3
            ambiguity = "low"
            tools = ["financial_api", "sec_edgar", "web_search", "news_sentiment", "fact_checker", "report_generator"]
            req_memory = False

        elif any(w in lower for w in ("compare", "versus", "vs", "cloud computing divisions", "market share")):
            qtype = QueryType.INDUSTRY_COMPARISON
            complexity = 3
            ambiguity = "low"
            tools = ["financial_api", "sec_edgar", "peer_comparison", "web_search", "calculation_engine", "report_generator"]
            req_memory = False

        elif any(w in lower for w in ("risk assessment", "risks", "regulatory risks", "operational risks")):
            qtype = QueryType.RISK_ASSESSMENT
            complexity = 2
            ambiguity = "low"
            tools = ["sec_edgar", "web_search", "news_sentiment", "financial_api", "report_generator"]
            req_memory = False

        elif any(w in lower for w in ("quarterly earnings", "earnings call", "consensus estimates", "beats/misses")):
            qtype = QueryType.EARNINGS_ANALYSIS
            complexity = 2
            ambiguity = "low"
            tools = ["financial_api", "earnings", "earnings_transcript", "web_search", "news_sentiment", "report_generator"]
            req_memory = False

        elif any(w in lower for w in ("profile", "overview", "executives")):
            qtype = QueryType.COMPANY_PROFILE
            complexity = 1
            ambiguity = "low"
            tools = ["company_profile", "financial_api", "web_search", "report_generator"]
            req_memory = False

        else:
            qtype = QueryType.UNKNOWN
            complexity = 2
            ambiguity = "medium"
            tools = ["web_search", "financial_api", "company_profile", "report_generator"]
            req_memory = False

        # Temporal Scope
        if any(w in lower for w in ("quarter", "q1", "q2", "q3", "q4", "recent earnings")):
            temporal = "quarterly"
        elif any(w in lower for w in ("history", "3-5 year", "historical", "trend")):
            temporal = "multi_year_historical"
        else:
            temporal = "current_period"

        return QueryAnalysis(
            original_query=query,
            query_type=qtype,
            complexity_score=complexity,
            ambiguity_level=ambiguity,
            target_tickers=tickers,
            temporal_scope=temporal,
            is_multi_company=is_multi,
            requires_memory=req_memory,
            rate_of_change_detected=rate_of_change,
            recommended_tools=tools,
        )
