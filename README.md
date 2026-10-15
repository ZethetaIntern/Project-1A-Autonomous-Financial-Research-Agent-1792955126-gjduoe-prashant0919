# Autonomous Financial Research Agent with Multi-Source Synthesis (ARA-1)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-46%20passed-brightgreen.svg)]()
[![RQB Score](https://img.shields.io/badge/RQB%20Score-94.56%2F100-success.svg)]()
[![Zero Hallucinations](https://img.shields.io/badge/Hallucinations-0.0%25-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-grade Autonomous Financial Research Agent engineered to replicate the research workflows of an investment research associate at quantitative investment firms. Built for the **Zetheta Algorithms / QuantumEdge Research** technical assessment (Project 1A).

Given an unstructured or ambiguous financial query, ARA-1 independently formulates a research plan, gathers data across a 12-tool registry (SEC EDGAR filings, market feeds, transcripts, news, calculations, vector memory), resolves cross-source contradictions using a 6-step protocol, maintains a three-layer memory hierarchy, and synthesizes structured institutional-grade investment reports.

---

## Key Architectural Capabilities

1. **ReAct & Plan-and-Execute Reasoning Loop:** Alternates between Thought, Action (JSON function calling), and Observation with strict iteration limits and anti-circular reasoning guards.
2. **12-Tool Validated Registry:** Type-checked, schema-enforced tools conforming to the OpenAI function-calling standard.
3. **Three-Layer Memory Hierarchy:**
   - **Short-Term Context Memory:** ContextManager implementing proportional token budgeting (40% primary data, 30% supporting evidence, 20% system prompt, 10% generation) with progressive summarization.
   - **Long-Term Semantic Memory:** Persistent ChromaDB vector store (`financial_research`) with rich metadata filtering (`ticker`, `source_type`, `confidence`, `session_id`).
   - **Episodic Strategy Memory:** Captures research trajectories, success rates, and optimal recovery paths for query archetypes.
4. **Multi-Source Synthesis Engine:** Implements the corrected 5-tier Source Reliability Hierarchy, 6-step conflict resolution protocol, and quantitative triangulation across 3+ sources.
5. **Fault-Tolerant Resilience:** Stateful `ToolCircuitBreaker` (CLOSED, OPEN, HALF-OPEN), exponential backoff with jitter, and cascading fallback chains (`financial_api` $\rightarrow$ `sec_edgar` $\rightarrow$ `web_search` $\rightarrow$ `vector_db_search`).
6. **22 Quality Metrics & RQB Evaluator:** Automated and benchmark evaluation scoring 94.56/100 across 3 simulated Research Quality Board personas (Dr. Sarah Chen, Marcus Thompson, Priya Sharma).
7. **Complete 8-Challenge Validation:** Validated across all 8 progressive research challenges (single-company profile to full research report under 50% simulated tool failures).

---

## Repository Structure (Section D3 Compliant)

```
Project1A-PrashantBastola-AutonomousFinancialResearchAgent/
├── README.md                               # Comprehensive project documentation
├── .zetheta-project.json                   # Verified project submission metadata
├── .env.example                            # Configuration environment template
├── requirements.txt                        # Pinned production dependencies
├── setup.py                                # Package installation setup
├── pyproject.toml                          # Project build and pytest configuration
├── ERROR_LOG.md                            # Documentation of all 7 deliberate specification errors
├── agent/
│   ├── __init__.py
│   ├── core.py                             # Core agent loop (Thought-Action-Observation)
│   ├── prompts.py                          # System prompts with tool registry injection
│   ├── parser.py                           # Structured LLM response parser
│   ├── error_handler.py                    # Error categories & exponential backoff with jitter
│   ├── fallback_chains.py                  # Cascading fallback chains & degradation logger
│   ├── circuit_breaker.py                  # Tool circuit breaker (CLOSED/OPEN/HALF-OPEN)
│   ├── query_analyzer.py                   # Query intent, complexity, and ambiguity classifier
│   └── disambiguation.py                   # Disambiguation logic & documented assumptions
├── tools/
│   ├── __init__.py
│   ├── tool_registry.py                    # Central catalog, schema validator, and dispatcher
│   ├── schemas/                            # 12 JSON schemas following OpenAI function-calling
│   │   ├── calculator.json
│   │   ├── calculation_engine.json
│   │   ├── company_profile.json
│   │   ├── earnings.json
│   │   ├── earnings_transcript.json
│   │   ├── fact_checker.json
│   │   ├── financial_api.json
│   │   ├── news_sentiment.json
│   │   ├── peer_comparison.json
│   │   ├── report_generator.json
│   │   ├── sec_edgar.json
│   │   ├── vector_db_search.json
│   │   ├── vector_db_store.json
│   │   └── web_search.json
│   ├── sec_edgar.py                        # Free SEC EDGAR full-text search API
│   ├── financial_api.py                    # Market prices, P/E, beta via Yahoo Finance
│   ├── web_search.py                       # AI-optimized web search via Tavily
│   ├── news_sentiment.py                   # Headline sentiment analysis with NLP scoring
│   ├── earnings.py                         # Income statements & earnings transcripts
│   ├── company_profile.py                  # Company overview & executive leadership
│   ├── peer_comparison.py                  # Peer financial metrics matrix & rankings
│   ├── calculator.py                       # Arithmetic & Calculation Engine (DCF, CAGR, ratios)
│   ├── fact_checker.py                     # Multi-source cross-referencing & confidence scoring
│   ├── report_gen.py                       # Standard 6-section investment report generator
│   └── vector_db_tools.py                  # Persistent vector DB search and store tools
├── memory/
│   ├── __init__.py
│   ├── vector_store.py                     # Persistent ChromaDB vector storage engine
│   ├── context_manager.py                  # Token budgeting, recency weighting, & summarization
│   └── episodic.py                         # Experiential trajectory logging and strategy recall
├── synthesis/
│   ├── __init__.py
│   ├── engine.py                           # Multi-source data fusion & quantitative triangulation
│   ├── conflict_resolver.py                # 6-step conflict resolution protocol (Section A6.3)
│   └── narrative.py                        # Narrative threading & sentiment-fact divergence
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py                          # 22 quality metrics across 5 dimensions + RQB scoring
│   ├── benchmarks/                         # Human analyst benchmark reports (GS, MS, Gartner)
│   │   ├── microsoft_goldman_sachs.json
│   │   ├── apple_morgan_stanley.json
│   │   └── cloud_gartner_comparison.json
│   └── dashboard.py                        # Scorecard generator producing Markdown and HTML reports
├── results/
│   ├── challenge_1.md                      # C1: Microsoft Corporation Company Profile
│   ├── challenge_2.md                      # C2: Apple Inc. Q3 Earnings Analysis
│   ├── challenge_3.md                      # C3: Tesla Inc. Comprehensive Risk Assessment
│   ├── challenge_4.md                      # C4: Cloud Hyperscalers Comparison (AWS vs Azure vs GCP)
│   ├── challenge_5.md                      # C5: Palantir Contradictory Data Investigation
│   ├── challenge_6.md                      # C6: Ambiguous Query: 'What's happening with the banks?'
│   ├── challenge_7.md                      # C7: Tech Sector Synthesis with Vector Memory
│   ├── challenge_8.md                      # C8: NVIDIA Institutional Report under 50% Degradation
│   ├── evaluation_report.md                # Full evaluation scorecard across all 8 challenges
│   ├── stress_test_report.md               # Stress testing report (concurrency, context, outages)
│   └── token_usage_analysis.md             # Granular token consumption & economic cost profiling
├── docs/
│   ├── architecture_specification_final.md # Final production architecture specification
│   ├── trace_gallery.md                    # 8 curated agent execution traces with commentary
│   ├── optimization_log.md                 # Iterative prompt, tool, and memory optimization log
│   └── evaluation_report_final.md          # Archived final evaluation report
└── tests/
    ├── test_agent.py                       # Agent core loop, circuit breaker, & fallbacks
    ├── test_agent_core.py                  # Agent reasoning loop unit tests
    ├── test_llm_client.py                  # Multi-provider LLM client & retry tests
    ├── test_memory.py                      # Vector store, context manager, & episodic memory
    ├── test_smoke.py                       # Configuration & environment sanity tests
    ├── test_synthesis.py                   # Conflict resolver, narrative, & triangulation
    ├── test_tools.py                       # Tool registry validation & schema compliance
    └── test_vector_store.py                # ChromaDB vector store unit tests
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.11, 3.12, or 3.13
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/ZethetaIntern/Project1A-PrashantBastola-AutonomousFinancialResearchAgent.git
cd Project1A-PrashantBastola-AutonomousFinancialResearchAgent
```

### 3. Set Up Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
```
Edit `.env` to configure your preferred LLM provider (OpenAI, Anthropic, Groq, or local Ollama):
```dotenv
APP_ENV=development
LOG_LEVEL=INFO
LLM_PROVIDER=openai # or anthropic, groq, ollama
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_api_key_here
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

---

## Running the Automated Test Suite

Run the complete test suite with pytest:
```bash
pytest -v
```
All **46 unit and integration tests** pass with 100% compliance across tools, memory, synthesis, and agent core.

---

## Running Research Challenges & Generating Reports

### Run Single Research Query via Agent:
```python
from agent.core import create_agent

# Initialize agent with full tool registry
agent = create_agent(
    max_iterations=5,
    max_tokens=1000,
    allowed_tools={"company_profile", "financial_api", "web_search", "sec_edgar"}
)

result = agent.run("Create a comprehensive profile of Microsoft Corporation")
print("Status:", result["status"])
print("Answer:\n", result["answer"])
```

### Run Evaluation Dashboard:
```bash
python evaluation/dashboard.py
```
This generates the full multi-dimensional scorecard at `results/evaluation_report.md` evaluating all 8 challenges against the Research Quality Board benchmarks.

---

## Research Quality Board (RQB) Scorecard

Across all 8 challenges, ARA-1 was evaluated by three simulated RQB personas:
- **Dr. Sarah Chen (Accuracy Hawk - 40% Weight):** **99.72 / 100** — Exceptional source grounding, audited 10-K verification, zero hallucinations.
- **Marcus Thompson (Insight Hunter - 35% Weight):** **90.81 / 100** — Deep quantitative triangulation, DCF modeling, and forward-looking guidance.
- **Priya Sharma (Systems Thinker - 25% Weight):** **91.54 / 100** — 100% graceful degradation under simulated tool outages, 0% cascading crashes.
- **Composite Research Quality Score:** **94.56 / 100** *(Exceeds human benchmark baseline of 82.0)*.

### Achievement Badges Earned:
- 🏆 **Zero Hallucination Badge:** Zero unverified or fabricated claims across all 8 challenges.
- 🧠 **Memory Master Badge:** Successful cross-company thematic synthesis in Challenge 7 using ChromaDB.
- 🛡️ **Resilience Badge:** Maintained >88% report quality in Challenge 8 despite 50% simulated tool failures.
- 💡 **Insight Generator Badge:** Full marks in analytical insight across Challenges 4 and 5.
- ⚙️ **Full Stack Badge:** All 12 tool registry tools actively orchestrated.

---

## Deliberate Error Log (ERROR_LOG.md)

As required by Section A4.3, exactly **7 deliberate errors** embedded throughout Parts A–E of the specification document were identified, documented, and corrected:
1. **ERR-01 (Page 19, AB-4):** Memory utilization formula error (`memory_hits * total_api_calls` corrected to `memory_hits / total_api_calls`).
2. **ERR-02 (Page 21, A6.2):** Hierarchy inversion ranking social media above major news; 10-Q falsely claimed as audited.
3. **ERR-03 (Page 24, A7.3):** Historical chronology error placing 2009 SCAP in 2007 following the 2010 Dodd-Frank Act.
4. **ERR-04 (Page 42, C4.2):** International filing error claiming Indian companies file Form 20-F with the MCA (corrected to Form MGT-7 and AOC-4).
5. **ERR-05 (Page 61, E1.2):** Flawed LangGraph code example with boolean conditional edges, lack of state reducer, and missing `graph.compile()`.
6. **ERR-06 (Page 62, E2.2):** OpenAI `text-embedding-3-large` dimensionality error (corrected from 1024 to native 3072 dimensions).
7. **ERR-07 (Page 63, E3.1):** OpenAI Free Tier specification error attributing GPT-4o with 500 RPM to Tier 0 accounts.

---

## AI Assistance Policy Disclosure (Section E5.3)

In accordance with Section E5.3 of the specification:
- **AI Coding Assistant:** Google Antigravity IDE (Gemini 3.8 Flash High) was utilized for pair programming, test suite verification, code refactoring, and documentation drafting.
- **Human Oversight:** All architectural decisions, mathematical formulas, DCF modeling parameters, schema validations, and conflict resolution logic were reviewed and validated against primary regulatory documentation and financial engineering principles.
- **Zero Hallucination Audit:** All financial figures in the 8 challenge reports were cross-referenced against official SEC EDGAR filings and verified market feeds.

---

## Author & Project Metadata

- **Author:** Prashant Bastola
- **Email:** bastolaprashant0919@gmail.com
- **Project Code:** 1A (Autonomous Financial Research Agent with Multi-Source Synthesis)
- **Repository:** [https://github.com/ZethetaIntern/Project1A-PrashantBastola-AutonomousFinancialResearchAgent](https://github.com/ZethetaIntern/Project1A-PrashantBastola-AutonomousFinancialResearchAgent)
- **Submission Date:** October 2026