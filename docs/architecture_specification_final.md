# Autonomous Financial Research Agent (ARA-1)
## Final Production Architecture Specification

**Project:** Project 1A — Autonomous Financial Research Agent with Multi-Source Synthesis  
**Author:** Prashant Bastola  
**Version:** 2.0.0 (Final Build Phase)  
**Status:** Completed Production Architecture  
**Repository:** `Project1A-PrashantBastola-AutonomousFinancialResearchAgent`  
**Affiliation:** QuantumEdge Research / Zetheta Algorithms  

---

## 1. Executive Summary & Production Status

The Autonomous Financial Research Agent (ARA-1) is a production-grade agentic AI system engineered to replicate the end-to-end workflow of an equity research associate at quantitative investment firms. Given an unstructured or ambiguous research query, the agent autonomously formulates a structured investigation plan, coordinates multi-source data ingestion across a 12-tool registry, resolves cross-source contradictions using a 6-step protocol, maintains three layers of working and persistent memory, and delivers professional, citation-grounded research reports.

### Architecture Highlights:
- **Reasoning Loop:** Hybrid Plan-and-Execute with ReAct-style iterative refinement and bounded iteration limits.
- **Tool Registry:** 12 fully typed, schema-validated tools compliant with OpenAI function-calling specifications.
- **Three-Layer Memory:**
  1. *Short-Term Context Memory:* Token-budgeted context manager allocating 40% primary, 30% supporting, 20% prompt, 10% generation space with progressive summarization.
  2. *Long-Term Semantic Memory:* Persistent ChromaDB vector store with rich metadata filtering (ticker, source_type, confidence, session).
  3. *Episodic Strategy Memory:* Experience store recording query types, tool trajectory frequencies, failure points, and optimal recovery paths.
- **Multi-Source Synthesis Engine:** Implements the corrected source reliability hierarchy (Tier 1: Audited 10-K / reviewed 10-Q down to Tier 5: Unverified social forums), quantitative triangulation across 3+ sources, and sentiment-fact divergence detection.
- **Fault-Tolerant Infrastructure:** ToolCircuitBreaker pattern (CLOSED, OPEN, HALF-OPEN), exponential backoff with random jitter, and cascading fallback chains guaranteeing zero unhandled crashes under 100% external API outages.
- **Evaluation Framework:** Automated and LLM-as-judge scoring across 22 quality metrics, benchmarked against senior analysts from Goldman Sachs, Morgan Stanley, and Gartner.

---

## 2. System Cognitive Loop & Orchestration

The cognitive cycle follows a strict StateGraph progression:

```
[ User Query ]
       │
       ▼
[ Query Analyzer & Disambiguator ] ──(Ambiguous?)──> [ Document Assumptions ]
       │                                                         │
       ▼                                                         ▼
[ Research Planner ] <───────────────────────────────────────────┘
       │
       ▼
┌──>[ ReAct Iterative Loop ]
│      │
│      ├─► Thought: Evaluate current evidence context & identify information gaps.
│      ├─► Action: Select optimal tool from registry with schema-validated JSON.
│      ├─► Circuit Breaker Check: If tool circuit is OPEN, cascade to Fallback Chain.
│      ├─► Execution: Run API / scraper / calculation engine with backoff & jitter.
│      └─► Observation: Ingest tool result, update ContextManager & prune if needed.
│      │
└─── (Iteration < Max Limit & Gaps Remain)
       │
       ▼
[ Multi-Source Synthesis Engine ]
       │
       ├─► 6-Step Conflict Resolution Protocol
       ├─► Quantitative Triangulation (3+ Sources)
       └─► Sentiment-Fact Divergence Detection
       │
       ▼
[ Fact Verification Pipeline ] ──(Discrepancy > 5%?)──> [ Flag for Review ]
       │
       ▼
[ Report Generator & Markdown Exporter ]
       │
       ▼
[ Episodic Memory Recording & Vector Store Ingestion ]
```

---

## 3. Tool Registry Architecture & Schemas

The system registers 12 dedicated tools in `tools/tool_registry.py`. Each tool defines strict JSON schemas in `tools/schemas/` enforcing types, enums, min/max constraints, and forbidden extraneous properties.

### Tool Catalog Summary

| Tool Name | Sub-Module | Primary Responsibility | Input Parameters | Output Format |
|---|---|---|---|---|
| `company_profile` | `tools/company_profile.py` | Corporate description, sector, industry, and leadership roster. | `ticker: str` | JSON profile object |
| `sec_edgar` | `tools/sec_edgar.py` | Full-text EDGAR filing retrieval (10-K, 10-Q, 8-K). | `ticker: str, filing_type: str, year: int?` | Filing accession, text, date |
| `financial_api` | `tools/financial_api.py` | Live & historical market prices, P/E, market cap, beta via Yahoo Finance. | `ticker: str` | Financial metrics JSON |
| `earnings` | `tools/earnings.py` | Income statement revenue, operating income, net income, EPS. | `ticker: str, fiscal_period: str?` | Period statement data |
| `earnings_transcript`| `tools/earnings.py` | Earnings call transcripts with speaker labels and Q&A. | `ticker: str, quarter: str, year: int` | Transcript text with speaker labels |
| `web_search` | `tools/web_search.py` | Real-time news, analyst commentary, and strategic updates via Tavily. | `query: str, max_results: int?` | URLs, titles, snippets |
| `news_sentiment` | `tools/news_sentiment.py` | Headline sentiment scoring using NLP polarity classification. | `ticker: str, max_articles: int?` | Sentiment label, score, articles |
| `peer_comparison` | `tools/peer_comparison.py` | Industry peer benchmarking across P/E, margins, and market cap. | `ticker: str, peer_tickers: list[str]` | Peer comparison matrix & rank |
| `calculator` | `tools/calculator.py` | Finite floating-point arithmetic with zero-division guards. | `operation: str, a: float, b: float` | Operation result dict |
| `calculation_engine` | `tools/calculator.py` | DCF intrinsic valuation, financial ratios (ROE, margins), and CAGR. | `calculation_type: str, inputs: dict` | Valuation result with steps |
| `fact_checker` | `tools/fact_checker.py` | Multi-source claim cross-referencing and confidence scoring. | `claim: str, sources: list[str]?` | Verification status & confidence |
| `report_generator` | `tools/report_gen.py` | Formats multi-source findings into 6-section investment report. | `company_name: str, ticker: str, findings: list` | Formatted Markdown report |
| `vector_db_search` | `tools/vector_db_tools.py`| Semantic query against persistent ChromaDB long-term memory. | `query: str, top_k: int, ticker: str?` | Document chunks with similarity |
| `vector_db_store` | `tools/vector_db_tools.py` | Ingests verified research finding into persistent vector store. | `content: str, ticker: str, source_type: str` | Stored document confirmation |

---

## 4. Memory Hierarchy & Context Management

### 4.1 Short-Term Working Memory (`memory/context_manager.py`)
To prevent context overflow and token inflation, `ContextManager` enforces proportional token budgets based on Section A8.2:
- **Primary Budget (40%):** SEC filings, audited balance sheets, income statements.
- **Supporting Budget (30%):** Web search snippets, press commentary, analyst opinions.
- **System Overhead (20%):** Prompt instructions and tool schemas.
- **Generation Budget (10%):** LLM generation space.

When a memory partition exceeds its allocated token budget, `_prune_partition()` sorts chunks by priority and recency, evicts the lowest-ranked items, and condenses them into a structured summary to preserve historical evidence.

### 4.2 Long-Term Semantic Memory (`memory/vector_store.py`)
Built on ChromaDB's persistent client, storing records with dense vector embeddings and rich metadata:
- `id`: Unique record identifier (UUID or ticker-prefixed accession).
- `content`: Extracted document chunk.
- `ticker`: Normalized ticker symbol.
- `source_type`: Canonical classification (`10-K`, `10-Q`, `8-K`, `earnings_call`, `news`, `analysis`).
- `date`: ISO-8601 UTC timestamp.
- `confidence`: Confidence score [0.0 - 1.0].
- `researcher_session`: Session identifier for auditability.

### 4.3 Episodic Memory (`memory/episodic.py`)
Maintains an experiential record of prior research sessions in `data/episodic_memory.json`. When a new query is received, the agent calls `get_strategy_recommendation(query_type)` to identify high-probability tool sequences, known failure modes, and tested fallback strategies.

---

## 5. Multi-Source Synthesis & Conflict Resolution

### 5.1 Corrected Source Reliability Hierarchy
Following the correction of deliberate error ERR-02:
1. **Tier 1 (Highest):** SEC filings (`Form 10-K` audited, `Form 10-Q` reviewed, `Form 8-K` material events).
2. **Tier 2:** Professional financial data APIs (Bloomberg, FactSet, Refinitiv, S&P Global, Yahoo Finance).
3. **Tier 3:** Direct corporate disclosures & transcripts (Management prepared remarks and analyst Q&A).
4. **Tier 4:** Institutional financial journalism (Reuters, Bloomberg News, Financial Times, Wall Street Journal).
5. **Tier 5 (Lowest):** Unverified social media, retail forums, and anonymous online commentary.

### 5.2 6-Step Conflict Resolution Protocol
1. **Conflict Detection:** Identifies discrepancies exceeding 5.0% tolerance in numerical figures.
2. **Source Tier Assessment:** Classifies conflicting sources into Tiers 1 through 5.
3. **Temporal Differencing:** Verifies whether conflicting figures represent different fiscal quarters or fiscal years.
4. **Restatement Identification:** Checks whether a subsequent filing restated prior-period historical financials.
5. **Highest-Tier Rule:** Prefers higher-tier authoritative sources if temporal or restatement analysis does not reconcile the figures.
6. **Conflict Documentation:** Formats transparent disclosure of the discrepancy and resolution rationale in the final report.

---

## 6. Fault Tolerance & Graceful Degradation

### 6.1 Tool Circuit Breakers (`agent/circuit_breaker.py`)
Each tool is monitored by a stateful circuit breaker:
- `CLOSED`: Normal operation. Each failure increments an internal counter.
- `OPEN`: If consecutive failures reach `failure_threshold` (default: 3), the circuit trips to `OPEN`. All subsequent calls fail fast without burning retry attempts or API credits.
- `HALF_OPEN`: After a cool-down period (default: 10s), the circuit allows a single trial request. Success resets to `CLOSED`; failure re-trips to `OPEN`.

### 6.2 Cascading Fallback Chains (`agent/fallback_chains.py`)
Primary tools are paired with multi-level fallback paths:
- `financial_api` $\rightarrow$ `sec_edgar` $\rightarrow$ `web_search` $\rightarrow$ `vector_db_search`
- `sec_edgar` $\rightarrow$ `web_search` $\rightarrow$ `vector_db_search`
- `earnings_transcript` $\rightarrow$ `earnings` $\rightarrow$ `web_search`

When a fallback is engaged, the agent automatically logs the event, applies a confidence penalty (0.15 per level), and appends a Graceful Degradation Disclosure to the report.

---

## 7. Quality Metrics Framework & Evaluation

The system is evaluated across **22 distinct metrics** grouped into 5 categories:
- **Category 1: Factual Accuracy (FA-1 to FA-5):** Numerical accuracy (>98%), citation accuracy (100%), temporal accuracy (100%), entity accuracy (100%), hallucination count (0).
- **Category 2: Completeness (CO-1 to CO-4):** Section coverage (100%), source diversity ($\ge 4$), temporal horizon ($\ge 3$ years), risk factor coverage ($\ge 80\%$).
- **Category 3: Analytical Depth (AD-1 to AD-4):** Insight density ($\ge 3$/page), cross-source synthesis ($\ge 5$), quantitative calculations ($\ge 10$), forward-looking analyses ($\ge 2$).
- **Category 4: Coherence & Structure (CS-1 to CS-4):** Logical flow ($\ge 4.5/5$), zero self-contradictions, executive summary quality ($\ge 4.5/5$), professional formatting (100%).
- **Category 5: Agent Behaviour (AB-1 to AB-5):** Tool efficiency ($\ge 70\%$), error recovery ($\ge 90\%$), planning quality ($\ge 4.5/5$), memory utilization ($\ge 0.30$), latency ($< 300\text{s}$).

### Research Quality Board (RQB) Weighting:
$$\text{Score} = 0.40 \times \text{Chen (Accuracy)} + 0.35 \times \text{Thompson (Insight)} + 0.25 \times \text{Sharma (Systems)}$$

---

## 8. Verified Deliberate Errors

All 7 deliberate specification errors (ERR-01 through ERR-07) have been identified, corrected in code, and verified in `ERROR_LOG.md`:
1. **ERR-01:** Corrected AB-4 formula from multiplication to division: `memory_hits / total_api_calls`.
2. **ERR-02:** Inverted flawed hierarchy ranking social media above major news; noted 10-Q is unaudited.
3. **ERR-03:** Fixed SCAP / Dodd-Frank chronology (SCAP occurred in 2009; Dodd-Frank enacted in 2010).
4. **ERR-04:** Corrected Indian MCA filing forms (Form MGT-7 and AOC-4 instead of US Form 20-F).
5. **ERR-05:** Fixed LangGraph StateGraph example (string conditional routing, state reducer, and compile call).
6. **ERR-06:** Corrected `text-embedding-3-large` native dimensionality from 1024 to 3072 dimensions.
7. **ERR-07:** Clarified OpenAI API tier policies (GPT-4o unavailable on Free Tier; requires funded Tier 1).
