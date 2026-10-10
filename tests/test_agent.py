"""Comprehensive tests for agent core loop, error handling, circuit breaker, fallbacks, and disambiguation."""

from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from agent.core import AgentError, FinancialResearchAgent
from agent.error_handler import ErrorHandler, ToolExecutionError
from agent.circuit_breaker import ToolCircuitBreaker, CircuitBreakerOpenError, CircuitState
from agent.fallback_chains import FallbackChainManager
from agent.query_analyzer import QueryAnalyzer, QueryType
from agent.disambiguation import QueryDisambiguator
from tools.tool_registry import ToolRegistry


def mock_response(text: str):
    return SimpleNamespace(text=text)


@pytest.fixture
def test_registry():
    registry = ToolRegistry()
    registry.register(
        name="company_profile",
        description="Profile",
        parameters={
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
        function=lambda ticker: {"ticker": ticker, "company_name": "Test Co", "data_source": "mock"},
    )
    registry.register(
        name="web_search",
        description="Search",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        function=lambda query: {"query": query, "results": ["Sample search result"]},
    )
    return registry


def test_agent_core_execution(test_registry):
    llm = Mock()
    llm.complete.side_effect = [
        mock_response('{"action": "execute", "name": "company_profile", "arguments": {"ticker": "MSFT"}}'),
        mock_response('{"type": "final", "answer": "Microsoft profile completed successfully."}'),
    ]
    llm.get_usage.return_value = {"input_tokens": 100, "output_tokens": 50}

    agent = FinancialResearchAgent(
        llm_client=llm,
        tool_registry=test_registry,
        max_iterations=3,
        allowed_tools={"company_profile", "web_search"},
    )

    result = agent.run("Profile Microsoft")
    assert result["status"] == "completed"
    assert "Microsoft profile completed successfully." in result["answer"]
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["tool"] == "company_profile"


def test_circuit_breaker_transitions():
    cb = ToolCircuitBreaker(
        tool_name="failing_api",
        failure_threshold=2,
        recovery_timeout_seconds=0.1,
    )

    def failing_call():
        raise ConnectionError("API connection reset")

    # Failure 1
    with pytest.raises(ConnectionError):
        cb.call(failing_call)
    assert cb.state == CircuitState.CLOSED

    # Failure 2 -> Trips to OPEN
    with pytest.raises(ConnectionError):
        cb.call(failing_call)
    assert cb.state == CircuitState.OPEN

    # While OPEN, immediate fast failure without invoking underlying call
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(failing_call)


def test_fallback_chains_execution(test_registry):
    fallback_mgr = FallbackChainManager(
        fallback_chains={"company_profile": ["web_search"]}
    )

    def failing_primary_then_fallback(tool_name: str, args: dict):
        if tool_name == "company_profile":
            return {"success": False, "error": "EDGAR API 503 unavailable"}
        return {"success": True, "data": {"found_via": "web_search", "query": args.get("ticker")}}

    res = fallback_mgr.execute_with_fallback(
        primary_tool="company_profile",
        tool_executor=failing_primary_then_fallback,
        arguments={"ticker": "AAPL"},
    )

    assert res.success is True
    assert res.was_fallback is True
    assert res.executed_tool == "web_search"
    assert res.effective_confidence < 1.0
    assert "Primary tool 'company_profile' failed" in res.degradation_note


def test_error_handler_backoff_and_metrics():
    handler = ErrorHandler(max_retries=2, base_delay=0.01)

    attempts = 0
    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise TimeoutError("Socket timeout")
        return "success"

    result = handler.execute_with_retry(flaky_func, context_name="flaky_test")
    assert result == "success"
    assert attempts == 2

    metrics = handler.get_recovery_metrics()
    assert metrics["recovered_errors"] == 1
    assert metrics["recovery_rate_pct"] == 100.0


def test_query_analyzer_and_disambiguation():
    analyzer = QueryAnalyzer()
    analysis = analyzer.analyze("What's happening with the banks?")

    assert analysis.query_type == QueryType.AMBIGUOUS_THEMATIC
    assert analysis.ambiguity_level == "high"
    assert analysis.complexity_score >= 3

    disambiguator = QueryDisambiguator()
    res = disambiguator.disambiguate(analysis)

    assert res.is_ambiguous is True
    assert len(res.documented_assumptions) >= 2
    assert any("Regional" in a or "commercial" in a for a in res.documented_assumptions)
    assert len(res.clarifying_questions) >= 1
