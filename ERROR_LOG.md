# Error Log — Autonomous Financial Research Agent

## Overview

According to the project specification (Part A, Section A4.3, Page 17):
> *"NOTE TO INTERN: This document contains exactly 7 deliberate factual or logical errors embedded throughout Parts A through E. Identifying these errors is part of your assessment. Each correctly identified error with a proper explanation earns bonus points. Errors range from incorrect formulas, wrong API specifications, flawed logic in code examples, to factual inaccuracies about financial concepts. You must document each error you find in your submission's ERROR_LOG.md file."*

All **7 deliberate errors** embedded across Parts A through E have been identified, analyzed, cross-referenced against authoritative documentation, and corrected below.

---

## Summary Matrix of Deliberate Errors

| ID | Location | Error Category | Summary of Deliberate Error | Impact | Required Correction | Status |
|---|---|---|---|---|---|---|
| **ERR-01** | Part A, Section A5.2, Page 19 (AB-4) | Incorrect Formula | Definition defines AB-4 as the ratio of memory hits to external API calls, but the formula states `memory_hits * total_api_calls`. | Multiplying hits by calls produces an inflated pseudo-count rather than a normalized efficiency ratio [0, 1+]. | Change multiplication to division: `memory_hits / total_api_calls` (with zero-division protection). | **Confirmed & Corrected** |
| **ERR-02** | Part A, Section A6.2, Page 21 | Flawed Logic / Concept Inversion | 1. Forms 10-K and 10-Q are both claimed as "audited".<br>2. Reliability Tier 4 lists unverified anonymous social media posts above Tier 5 (Major news outlets like Reuters and Bloomberg). | 1. Treating 10-Q as audited risks false confidence.<br>2. Prioritizing anonymous forum rumors over professional journalism compromises data integrity. | 1. Clarify that 10-Q filings are unaudited quarterly reviews.<br>2. Invert tiers: Tier 4 = Major news outlets; Tier 5 = Unverified social media / forums. | **Confirmed & Corrected** |
| **ERR-03** | Part A, Section A7.3, Page 24 | Factual Inaccuracy / Chronology | States that the first US bank stress tests under SCAP were conducted in 2007 following the Dodd-Frank Act. | Chronologically impossible: SCAP was conducted in spring 2009; Dodd-Frank was enacted in July 2010. | Correct chronology: SCAP occurred in 2009 under Federal Reserve authority; Dodd-Frank was enacted in 2010 establishing CCAR/DFAST. | **Confirmed & Corrected** |
| **ERR-04** | Part C, Section C4.2, Page 42 | Factual Inaccuracy / Regulatory Filing | States that Indian companies file annual returns using Form 20-F with the MCA (Ministry of Corporate Affairs), similar to the US 10-K. | Form 20-F is a US SEC filing for Foreign Private Issuers, NOT an Indian MCA filing. | In India, companies file Form MGT-7 (Annual Return) and Form AOC-4 (Financial Statements) with the MCA. | **Confirmed & Corrected** |
| **ERR-05** | Part E, Section E1.2, Page 61 | Flawed Logic in Code Example | LangGraph StateGraph example uses boolean keys `{True: 'executor', False: 'synthesizer'}` in `add_conditional_edges`, lacks loop termination state, and omits `graph.compile()`. | StateGraph cannot be invoked without compilation; boolean mapping fails internal string routing, causing unhandled runtime errors or infinite loops. | Use string routing keys, update state properly, and invoke `app = graph.compile()` before execution. | **Confirmed & Corrected** |
| **ERR-06** | Part E, Section E2.2, Page 62 | Wrong API / Model Specification | Claims `OpenAI text-embedding-3-large` has 1024 dimensions. | Developers setting up vector DB indexes with 1024 dimensions will encounter vector dimension mismatch errors when calling the API. | Correct dimension: Native dimensionality of `text-embedding-3-large` is 3072 dimensions (1536 for small, 1024 for Cohere embed-v3). | **Confirmed & Corrected** |
| **ERR-07** | Part E, Section E3.1, Page 63 | Wrong API Tier Specification | States GPT-4o has rate limits of "500 RPM, 30,000 TPM on free tier" and that new accounts receive $5 in free credits. | GPT-4o is not available on the OpenAI Free Tier (requires Usage Tier 1+); free tier limits are 3 RPM / 40,000 TPM for mini/legacy models; $5 credit was deprecated. | Note that GPT-4o requires a funded Tier 1 account; Free Tier (Tier 0) does not support GPT-4o. | **Confirmed & Corrected** |

---

## Detailed Error Analysis and Resolutions

### Error 1: AB-4 Memory Utilization Formula Error
- **Location:** Page 19, Section A5.2, Category 5 (Agent Behaviour), Metric AB-4
- **Original Text:**
  > *"AB-4: Memory Utilization – Whether the agent checks and uses long-term memory before making redundant external calls. Measured as the ratio of memory hits to total external API calls (higher is better, target: >=0.3). Note: This metric is calculated as memory_hits multiplied by total_api_calls."*
- **Error Identification:** A ratio is mathematical division ($A / B$), not multiplication ($A \times B$). If an agent has 3 memory hits and 10 API calls, multiplication gives $3 \times 10 = 30$, which completely distorts the metric and violates the stated target of $\ge 0.3$.
- **Resolution & Implementation:**
  In `evaluation/metrics.py`:
  ```python
  def calculate_memory_utilization(memory_hits: int, total_api_calls: int) -> float:
      if total_api_calls == 0:
          return 1.0 if memory_hits > 0 else 0.0
      return round(memory_hits / total_api_calls, 4)
  ```

---

### Error 2: Source Reliability Hierarchy Inversion & 10-Q Audited Claim
- **Location:** Page 21, Section A6.2, Tiered Source Trustworthiness
- **Original Text:**
  > *"1. Tier 1 (Highest Reliability): SEC filings (10-K, 10-Q) – legally mandated, audited, subject to criminal penalties for misrepresentation.*
  > *...*
  > *4. Tier 4: Social media posts and anonymous forum discussions – crowd-sourced but unverified and subject to manipulation.*
  > *5. Tier 5: Major news outlets (Reuters, Bloomberg News, Financial Times) – professional journalism with editorial oversight but may contain errors or bias."*
- **Error Identification:**
  1. **Audited Claim:** Form 10-Q quarterly reports are interim financial disclosures reviewed by independent auditors under SAS 100, but they are **unaudited**. Only Form 10-K annual reports contain audited financial statements. (The document's own glossary on page 70 contradicts this by correctly stating 10-Q is unaudited).
  2. **Hierarchy Inversion:** Social media and anonymous internet boards (Reddit, Twitter/X, StockTwits) are ranked as Tier 4, *above* Tier 5 major global financial journalism organizations (Reuters, Bloomberg, FT, WSJ). Relying on anonymous social posts over institutional journalism with editorial accountability is a severe operational risk.
- **Resolution & Implementation:**
  In `synthesis/conflict_resolver.py`:
  - Tier 1: Legally mandated SEC filings (10-K audited, 10-Q reviewed)
  - Tier 2: Professional financial data providers (Bloomberg, FactSet, Refinitiv)
  - Tier 3: Direct management disclosures & transcripts (Earnings calls, 8-K)
  - Tier 4: Major financial news organizations (Reuters, Bloomberg News, FT, WSJ)
  - Tier 5 (Lowest): Unverified social media, retail forums, and anonymous commentary.

---

### Error 3: SCAP Stress Tests and Dodd-Frank Act Chronological Inversion
- **Location:** Page 24, Section A7.3, Handling Ambiguous Queries
- **Original Text:**
  > *"Historical context matters for disambiguation. A query about 'bank stress tests' in 2007 likely refers to the European Banking Authority's stress test programme, while the same query in 2009 likely refers to the US Federal Reserve's Supervisory Capital Assessment Program (SCAP) conducted in that year. The agent should use temporal context to disambiguate. Note: The first US bank stress tests under SCAP were conducted in 2007 following the Dodd-Frank Act."*
- **Error Identification:**
  - The Supervisory Capital Assessment Program (SCAP) was conducted by the Federal Reserve from February to May **2009** to stabilize the 19 largest US bank holding companies following the September 2008 financial crisis.
  - The Dodd-Frank Wall Street Reform and Consumer Protection Act was passed on **July 21, 2010**, more than a year *after* SCAP.
  - Stress tests mandated under Dodd-Frank are the Comprehensive Capital Analysis and Review (CCAR) and Dodd-Frank Act Stress Testing (DFAST), initiated in 2011.
- **Resolution & Implementation:**
  In `agent/disambiguation.py`:
  The temporal knowledge base correctly indexes SCAP as 2009, Dodd-Frank enactment as July 2010, and CCAR/DFAST starting in 2011.

---

### Error 4: Indian Regulatory Filing Form 20-F vs MCA Requirements
- **Location:** Page 42, Section C4.2, Case Study 4 (India's Regulatory Intelligence Challenge)
- **Original Text:**
  > *"Filing format differences: Indian companies file annual returns using Form 20-F with the MCA (Ministry of Corporate Affairs), similar to the 10-K filing in the US system. The agent must be configured to handle both formats."*
- **Error Identification:**
  - Form 20-F is an SEC form submitted by non-US foreign private issuers trading on US exchanges (e.g., Infosys or HDFC Bank ADRs on the NYSE).
  - Indian domestic companies incorporated under the Companies Act, 2013 file their statutory documents with the Ministry of Corporate Affairs (MCA) using:
    - **Form MGT-7 / MGT-7A**: Annual Return
    - **Form AOC-4 / AOC-4 XBRL**: Financial Statements and Board's Report
- **Resolution & Implementation:**
  Documented in architecture and query analyzer to ensure appropriate jurisdictional schema mapping.

---

### Error 5: Flawed LangGraph Plan-and-Execute Code Example
- **Location:** Page 61, Section E1.2, LangGraph Overview
- **Original Text:**
  ```python
  from langgraph.graph import StateGraph, END
  from typing import TypedDict, List
  class ResearchState(TypedDict):
      query: str
      plan: List[str]
      current_step: int
      gathered_data: dict
      draft_report: str
      verified_report: str

  graph = StateGraph(ResearchState)
  graph.add_node('planner', plan_research)
  graph.add_node('executor', execute_step)
  graph.add_node('synthesizer', synthesize_findings)
  graph.add_node('verifier', verify_facts)
  graph.add_node('reporter', generate_report)

  graph.set_entry_point('planner')
  graph.add_edge('planner', 'executor')
  graph.add_conditional_edges('executor',
      should_continue,
      {True: 'executor', False: 'synthesizer'})
  graph.add_edge('synthesizer', 'verifier')
  graph.add_edge('verifier', 'reporter')
  graph.add_edge('reporter', END)
  ```
- **Error Identification:**
  1. `graph.compile()` is never called: A `StateGraph` instance cannot be run; it must be compiled into a `CompiledStateGraph` via `app = graph.compile()`.
  2. Conditional Edge Type Mismatch: `add_conditional_edges` router functions must return keys matching the routing dictionary. Using boolean values `{True: ..., False: ...}` causes runtime typing issues with LangGraph's internal string edge mappings. Strings like `{"continue": "executor", "complete": "synthesizer"}` are required.
  3. Lack of loop safety: The `ResearchState` lacks state reducers (such as `Annotated[list, operator.add]` or step increment tracking), risking uncontrolled recursion without a safe exit condition.
- **Resolution & Implementation:**
  Correct LangGraph architecture is implemented with proper string condition routing, iteration tracking, and compilation.

---

### Error 6: OpenAI text-embedding-3-large Dimensionality Error
- **Location:** Page 62, Section E2.2, Recommended Embedding Models
- **Original Text:**
  > *"OpenAI text-embedding-3-large: 1024 dimensions, $0.13 per million tokens. Higher quality but 6.5x more expensive. Use only if small model shows retrieval quality issues."*
- **Error Identification:**
  - OpenAI's `text-embedding-3-large` has a default native dimensionality of **3072 dimensions**, not 1024.
  - `text-embedding-3-small` outputs 1536 dimensions.
  - Cohere `embed-v3` outputs 1024 dimensions.
  - While `text-embedding-3-large` supports dimension shortening via an optional `dimensions` parameter, asserting its specification as 1024 is factually wrong and causes vector DB dimension mismatch errors if an index is provisioned with 1024 slots for 3072 embeddings.
- **Resolution & Implementation:**
  In `memory/vector_store.py` and `config/settings.py`, ChromaDB and embedding models configure the appropriate native dimensions (384 for sentence-transformers, 1536 for small, 3072 for large).

---

### Error 7: OpenAI API Free Tier Model & Rate Limit Specification Error
- **Location:** Page 63, Section E3.1, LLM API Providers - OpenAI
- **Original Text:**
  > *"Model: GPT-4o or GPT-4o-mini for the reasoning engine... Rate Limits: GPT-4o: 500 RPM (requests per minute), 30,000 TPM (tokens per minute) on free tier."*
- **Error Identification:**
  1. **Model Availability:** GPT-4o has never been accessible on the OpenAI API Free Tier (Tier 0). Accessing flagship models like GPT-4o requires at least Usage Tier 1 (depositing at least $5).
  2. **Rate Limit Inaccuracy:** The OpenAI Free Tier rate limits are 3 RPM and 40,000 TPM for eligible miniature or legacy models; 500 RPM / 30,000 TPM represents a paid tier quota (Tier 1/2), not the Free Tier.
  3. **Account Credits:** OpenAI discontinued the automatic $5 free credit grant for new API accounts in 2023.
- **Resolution & Implementation:**
  Architecture and configuration support multi-provider fallback (OpenAI, Anthropic, Groq, Ollama) and gracefully handle tier restrictions and rate limiting via exponential backoff with jitter and circuit breaking.
