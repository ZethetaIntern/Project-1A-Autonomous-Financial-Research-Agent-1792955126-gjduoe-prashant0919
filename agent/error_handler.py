"""Error handling, categorization, and exponential backoff retry logic."""

import logging
import random
import time
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Canonical classification of agent errors (Section A4.2)."""

    TOOL_EXECUTION = "tool_execution"  # Network, timeouts, rate limits, API 500/503
    REASONING = "reasoning"            # Parsing failure, circular reasoning, schema violation
    DATA_QUALITY = "data_quality"      # Stale data, unit confusion, format mismatch


class ResearchAgentError(Exception):
    """Base exception for research agent errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.TOOL_EXECUTION,
        recoverable: bool = True,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.recoverable = recoverable
        self.details = details or {}


class ToolExecutionError(ResearchAgentError):
    """Raised when an external tool or API fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, category=ErrorCategory.TOOL_EXECUTION, recoverable=True, details=details)


class ReasoningError(ResearchAgentError):
    """Raised when the LLM produces malformed or circular actions."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, category=ErrorCategory.REASONING, recoverable=False, details=details)


class DataQualityError(ResearchAgentError):
    """Raised when data cannot be validated or contains severe inconsistencies."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, category=ErrorCategory.DATA_QUALITY, recoverable=True, details=details)


class ErrorHandler:
    """Manages error classification, backoff retries with jitter, and recovery tracking."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 16.0) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.recovered_errors: list[dict[str, Any]] = []
        self.unrecovered_errors: list[dict[str, Any]] = []

    def execute_with_retry(
        self,
        operation: Callable[[], Any],
        context_name: str = "operation",
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> Any:
        """Execute a callable with exponential backoff and jitter (Section A4.3)."""
        attempt = 0
        while True:
            try:
                attempt += 1
                return operation()
            except retryable_exceptions as exc:
                if attempt > self.max_retries:
                    self.unrecovered_errors.append({
                        "context": context_name,
                        "attempts": attempt,
                        "error": str(exc),
                        "type": type(exc).__name__,
                    })
                    logger.error("Operation '%s' failed after %d attempts: %s", context_name, attempt, exc)
                    raise

                # Exponential backoff with jitter: delay = base * 2^(attempt-1) + jitter(0, 0.5)
                backoff = min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))
                jitter = random.uniform(0.0, 0.5)
                delay = backoff + jitter

                logger.warning(
                    "Attempt %d/%d for '%s' failed: %s. Retrying in %.2f seconds.",
                    attempt,
                    self.max_retries + 1,
                    context_name,
                    exc,
                    delay,
                )
                time.sleep(delay)
                self.recovered_errors.append({
                    "context": context_name,
                    "attempt": attempt,
                    "error": str(exc),
                })

    def get_recovery_metrics(self) -> dict[str, Any]:
        """Compute error recovery statistics (Metric AB-2)."""
        recovered = len(self.recovered_errors)
        unrecovered = len(self.unrecovered_errors)
        total = recovered + unrecovered

        rate = (recovered / total) if total > 0 else 1.0
        return {
            "total_errors": total,
            "recovered_errors": recovered,
            "unrecovered_errors": unrecovered,
            "recovery_rate_pct": round(rate * 100, 2),
            "target_met": rate >= 0.90,  # Target is >=90%
        }
