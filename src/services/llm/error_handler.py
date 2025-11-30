"""Error handling with circuit breaker pattern for LLM providers."""

import asyncio
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar
from uuid import UUID, uuid4

from pydantic import Field

from src.models.base import BrainForgeBaseModel, TimestampMixin
from src.services.llm.base import LLMError, LLMProviderError, LLMTimeoutError


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"      # Circuit is open, requests are blocked
    HALF_OPEN = "HALF_OPEN"  # Testing if service has recovered


class CircuitBreakerConfig(BrainForgeBaseModel):
    """Configuration for circuit breaker."""

    failure_threshold: int = Field(5, ge=1, description="Number of failures before opening circuit")
    reset_timeout: int = Field(60, ge=1, description="Timeout before attempting to close circuit (seconds)")
    timeout_duration: int = Field(30, ge=1, description="Request timeout duration (seconds)")
    max_retries: int = Field(3, ge=0, description="Maximum number of retries")
    retry_delay: float = Field(1.0, ge=0.0, description="Delay between retries (seconds)")
    health_check_interval: int = Field(30, ge=1, description="Health check interval (seconds)")


class CircuitBreakerMetrics(BrainForgeBaseModel, TimestampMixin):
    """Metrics for circuit breaker monitoring."""

    id: UUID = Field(default_factory=uuid4)
    provider_name: str = Field(..., description="Name of the LLM provider")
    total_requests: int = Field(0, description="Total number of requests")
    successful_requests: int = Field(0, description="Number of successful requests")
    failed_requests: int = Field(0, description="Number of failed requests")
    consecutive_failures: int = Field(0, description="Consecutive failures")
    last_failure_time: float | None = Field(None, description="Timestamp of last failure")
    last_success_time: float | None = Field(None, description="Timestamp of last success")
    state: CircuitBreakerState = Field(CircuitBreakerState.CLOSED, description="Current circuit state")
    constitutional_audit: dict[str, Any] = Field(default_factory=dict)

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


T = TypeVar("T")


class CircuitBreaker:
    """Circuit breaker implementation for LLM providers."""

    def __init__(self, provider_name: str, config: CircuitBreakerConfig | None = None):
        """Initialize circuit breaker."""
        self.provider_name = provider_name
        self.config = config or CircuitBreakerConfig()
        self.metrics = CircuitBreakerMetrics(provider_name=provider_name)
        self._state = CircuitBreakerState.CLOSED
        self._last_state_change = time.time()
        self._lock = asyncio.Lock()
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._reset_timeout = self.config.reset_timeout

    @property
    def state(self) -> str:
        """Get current state as string."""
        return self._state.value

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    @property
    def last_failure_time(self) -> float | None:
        """Get last failure time."""
        return self._last_failure_time

    @property
    def reset_timeout(self) -> int:
        """Get reset timeout."""
        return self._reset_timeout

    def can_execute(self) -> bool:
        """Check if circuit breaker allows execution."""
        if self._state == CircuitBreakerState.CLOSED:
            return True
        elif self._state == CircuitBreakerState.OPEN:
            # Check if reset timeout has passed
            if self._last_failure_time and time.time() - self._last_failure_time > self._reset_timeout:
                self._state = CircuitBreakerState.HALF_OPEN
                self._last_state_change = time.time()
                return True
            return False
        elif self._state == CircuitBreakerState.HALF_OPEN:
            return True
        return False

    def record_failure(self) -> None:
        """Record a failure (for testing purposes)."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.config.failure_threshold:
            self._state = CircuitBreakerState.OPEN
            self._last_state_change = time.time()

    def record_success(self) -> None:
        """Record a success (for testing purposes)."""
        self._failure_count = 0
        self._last_failure_time = None
        if self._state in [CircuitBreakerState.OPEN, CircuitBreakerState.HALF_OPEN]:
            self._state = CircuitBreakerState.CLOSED
            self._last_state_change = time.time()

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            await self._check_state()

            if self._state == CircuitBreakerState.OPEN:
                raise LLMProviderError(
                    f"Circuit breaker is OPEN for {self.provider_name}. "
                    f"Last failure: {self.metrics.last_failure_time}"
                )

            self.metrics.total_requests += 1

            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout_duration
                )

                await self._on_success()
                return result

            except TimeoutError:
                await self._on_failure(LLMTimeoutError(f"Request timeout for {self.provider_name}"))
                raise
            except Exception as e:
                await self._on_failure(e)
                raise

    async def _check_state(self) -> None:
        """Check and update circuit breaker state."""
        current_time = time.time()

        if self._state == CircuitBreakerState.OPEN:
            # Check if reset timeout has passed
            if current_time - self._last_state_change >= self.config.reset_timeout:
                self._state = CircuitBreakerState.HALF_OPEN
                self._last_state_change = current_time
                self.metrics.state = self._state

        elif self._state == CircuitBreakerState.HALF_OPEN:
            # Stay in half-open state for health checks
            pass

    async def _on_success(self) -> None:
        """Handle successful request."""
        self.metrics.successful_requests += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = time.time()

        if self._state == CircuitBreakerState.HALF_OPEN:
            self._state = CircuitBreakerState.CLOSED
            self._last_state_change = time.time()
            self.metrics.state = self._state

        # Update constitutional audit
        self.metrics.constitutional_audit.update({
            "last_success": self.metrics.last_success_time,
            "state_transition": "success_recovery" if self._state == CircuitBreakerState.CLOSED else "normal"
        })

    async def _on_failure(self, error: Exception) -> None:
        """Handle failed request."""
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.last_failure_time = time.time()

        if (self.metrics.consecutive_failures >= self.config.failure_threshold and
            self._state != CircuitBreakerState.OPEN):
            self._state = CircuitBreakerState.OPEN
            self._last_state_change = time.time()
            self.metrics.state = self._state

        # Update constitutional audit
        self.metrics.constitutional_audit.update({
            "last_failure": self.metrics.last_failure_time,
            "error_type": type(error).__name__,
            "consecutive_failures": self.metrics.consecutive_failures,
            "state_transition": "circuit_opened" if self._state == CircuitBreakerState.OPEN else "failure_counted"
        })

    async def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current metrics."""
        return self.metrics

    async def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        async with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._last_state_change = time.time()
            self.metrics.state = self._state
            self.metrics.consecutive_failures = 0
            self.metrics.constitutional_audit.update({
                "manual_reset": True,
                "reset_time": time.time()
            })


class RetryStrategy(BrainForgeBaseModel):
    """Retry strategy configuration."""

    max_retries: int = Field(3, ge=0, description="Maximum number of retries")
    base_delay: float = Field(1.0, ge=0.0, description="Base delay between retries (seconds)")
    max_delay: float = Field(10.0, ge=0.0, description="Maximum delay between retries (seconds)")
    jitter: bool = Field(True, description="Add jitter to retry delays")
    backoff_factor: float = Field(2.0, ge=1.0, description="Exponential backoff factor")

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.base_delay * (self.backoff_factor ** attempt)

        if self.jitter:
            # Add jitter: random value between 0.5 and 1.5 times the base delay
            import random
            jitter_factor = 0.5 + random.random()  # 0.5 to 1.5
            delay *= jitter_factor

        return min(delay, self.max_delay)


class ErrorHandler:
    """Comprehensive error handler for LLM operations."""

    def __init__(self, circuit_breaker: CircuitBreaker, retry_strategy: RetryStrategy | None = None):
        """Initialize error handler."""
        self.circuit_breaker = circuit_breaker
        self.retry_strategy = retry_strategy or RetryStrategy()

    async def execute_with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic and circuit breaker protection."""
        last_error = None

        for attempt in range(self.retry_strategy.max_retries + 1):
            try:
                return await self.circuit_breaker.execute(func, *args, **kwargs)
            except Exception as e:
                last_error = e

                # Don't retry if circuit breaker is open
                if (isinstance(e, LLMProviderError) and
                    "Circuit breaker is OPEN" in str(e)):
                    break

                # Don't retry on certain error types
                if isinstance(e, (LLMTimeoutError,)):
                    if attempt == self.retry_strategy.max_retries:
                        break
                    # Continue to retry

                # Wait before retry (except for last attempt)
                if attempt < self.retry_strategy.max_retries:
                    delay = self.retry_strategy.calculate_delay(attempt)
                    await asyncio.sleep(delay)

        # All retries failed
        if last_error:
            raise last_error
        else:
            raise LLMError("All retry attempts failed without specific error")

    async def handle_operation(self, func: Callable[..., T], max_retries: int | None = None) -> T:
        """Handle an operation with error handling and retry logic."""
        try:
            if max_retries is not None:
                # Create a temporary retry strategy for this operation
                temp_strategy = RetryStrategy(max_retries=max_retries)
                original_strategy = self.retry_strategy
                self.retry_strategy = temp_strategy
                try:
                    return await self.execute_with_retry(func)
                finally:
                    self.retry_strategy = original_strategy
            else:
                return await self.execute_with_retry(func)
        except Exception:
            # Record failure in circuit breaker
            self.circuit_breaker.record_failure()
            raise

    async def get_error_metrics(self) -> dict[str, Any]:
        """Get comprehensive error metrics."""
        metrics = await self.circuit_breaker.get_metrics()

        return {
            "provider_name": self.circuit_breaker.provider_name,
            "circuit_state": metrics.state.value,
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "failed_requests": metrics.failed_requests,
            "failure_rate": metrics.failure_rate,
            "success_rate": metrics.success_rate,
            "consecutive_failures": metrics.consecutive_failures,
            "last_failure_time": metrics.last_failure_time,
            "last_success_time": metrics.last_success_time,
            "retry_strategy": self.retry_strategy.model_dump(),
            "constitutional_audit": metrics.constitutional_audit
        }


class FallbackStrategy(BrainForgeBaseModel):
    """Fallback strategy configuration."""

    enabled: bool = Field(True, description="Enable fallback to alternative providers")
    fallback_order: list[str] = Field(default_factory=list, description="Order of fallback providers")
    max_fallback_depth: int = Field(2, ge=0, description="Maximum depth of fallback attempts")

    async def get_next_fallback(self, current_provider: str, attempted_providers: list[str]) -> str | None:
        """Get next fallback provider in sequence."""
        if not self.enabled or not self.fallback_order:
            return None

        # Find current provider in fallback order
        try:
            current_index = self.fallback_order.index(current_provider)
        except ValueError:
            current_index = -1

        # Get next available provider that hasn't been attempted
        for next_index in range(current_index + 1, len(self.fallback_order)):
            next_provider = self.fallback_order[next_index]
            if next_provider not in attempted_providers:
                return next_provider

        return None


class MultiProviderErrorHandler:
    """Error handler for multiple LLM providers with fallback support."""

    def __init__(self, provider_handlers: dict[str, ErrorHandler], fallback_strategy: FallbackStrategy):
        """Initialize multi-provider error handler."""
        self.provider_handlers = provider_handlers
        self.fallback_strategy = fallback_strategy

    async def execute_with_fallback(self, primary_provider: str, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with fallback to alternative providers."""
        attempted_providers = [primary_provider]
        last_error = None

        for depth in range(self.fallback_strategy.max_fallback_depth + 1):
            current_provider = attempted_providers[-1]

            if current_provider not in self.provider_handlers:
                raise LLMError(f"Provider handler not found: {current_provider}")

            handler = self.provider_handlers[current_provider]

            try:
                return await handler.execute_with_retry(func, *args, **kwargs)
            except Exception as e:
                last_error = e

                # Get next fallback provider
                next_provider = await self.fallback_strategy.get_next_fallback(
                    current_provider, attempted_providers
                )

                if not next_provider:
                    break

                attempted_providers.append(next_provider)

        # All providers failed
        error_details = {
            "attempted_providers": attempted_providers,
            "last_error": str(last_error) if last_error else "Unknown error",
            "error_type": type(last_error).__name__ if last_error else "Unknown"
        }

        raise LLMProviderError(
            f"All providers failed: {attempted_providers}. Last error: {last_error}",
            details=error_details
        )

    async def get_comprehensive_metrics(self) -> dict[str, Any]:
        """Get metrics for all providers."""
        metrics = {}

        for provider_name, handler in self.provider_handlers.items():
            metrics[provider_name] = await handler.get_error_metrics()

        return {
            "total_providers": len(self.provider_handlers),
            "providers": metrics,
            "fallback_strategy": self.fallback_strategy.model_dump()
        }
