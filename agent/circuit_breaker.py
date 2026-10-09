"""Circuit breaker pattern preventing cascading failures across agent tool executions."""

import logging
import time
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Possible states for a circuit breaker."""

    CLOSED = "closed"          # Healthy, traffic flows normally
    OPEN = "open"              # Tripped, requests fail fast to prevent cascading overload
    HALF_OPEN = "half_open"    # Testing recovery with trial requests


class CircuitBreakerOpenError(RuntimeError):
    """Raised when an operation is attempted while the circuit breaker is OPEN."""


class ToolCircuitBreaker:
    """Monitors failures for a specific tool and trips when thresholds are exceeded."""

    def __init__(
        self,
        tool_name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 10.0,
        success_threshold: int = 1,
    ) -> None:
        self.tool_name = tool_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute the function protected by the circuit breaker."""
        now = time.monotonic()

        # Check if an OPEN circuit has passed its recovery timeout
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.recovery_timeout_seconds:
                logger.info(
                    "Circuit breaker for '%s' transitioned from OPEN to HALF_OPEN (timeout elapsed)",
                    self.tool_name,
                )
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                remaining = self.recovery_timeout_seconds - (now - self.last_failure_time)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker for tool '{self.tool_name}' is OPEN. "
                    f"Failing fast to protect retry budget. Retry in {remaining:.1f}s."
                )

        try:
            result = func(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as exc:
            self._handle_failure(exc)
            raise

    def _handle_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker for '%s' recovered to CLOSED.", self.tool_name)
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on successful normal operation
            self.failure_count = 0

    def _handle_failure(self, exc: Exception) -> None:
        self.last_failure_time = time.monotonic()
        self.failure_count += 1
        logger.warning(
            "Circuit breaker for '%s' recorded failure #%d: %s",
            self.tool_name,
            self.failure_count,
            exc,
        )

        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                "Circuit breaker for '%s' TRIPPED to OPEN state (%d failures).",
                self.tool_name,
                self.failure_count,
            )


class CircuitBreakerRegistry:
    """Manages circuit breakers for all registered tools."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: float = 10.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._breakers: dict[str, ToolCircuitBreaker] = {}

    def get_breaker(self, tool_name: str) -> ToolCircuitBreaker:
        """Get or initialize a breaker for a tool."""
        if tool_name not in self._breakers:
            self._breakers[tool_name] = ToolCircuitBreaker(
                tool_name=tool_name,
                failure_threshold=self.failure_threshold,
                recovery_timeout_seconds=self.recovery_timeout_seconds,
            )
        return self._breakers[tool_name]

    def is_available(self, tool_name: str) -> bool:
        """Check whether a tool is currently eligible for calls."""
        breaker = self.get_breaker(tool_name)
        if breaker.state == CircuitState.CLOSED:
            return True
        if breaker.state == CircuitState.HALF_OPEN:
            return True
        # If open, check if timeout elapsed
        return (time.monotonic() - breaker.last_failure_time) >= breaker.recovery_timeout_seconds
