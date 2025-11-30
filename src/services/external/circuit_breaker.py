"""Circuit breaker pattern implementation for resilient external API calls."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests are blocked
    HALF_OPEN = "half_open"  # Testing if service is recovering


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5           # Number of failures to open circuit
    success_threshold: int = 3           # Number of successes to close circuit
    timeout: int = 60                    # Time in seconds to wait before half-open
    reset_timeout: int = 300             # Time in seconds to reset failure count
    half_open_max_requests: int = 1      # Max requests in half-open state


class CircuitBreaker:
    """Circuit breaker implementation for managing external service dependencies."""

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None
        self.last_state_change: float = time.time()

        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.circuit_opens = 0

    def is_open(self) -> bool:
        """Check if circuit is open."""
        if self.state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if time.time() - self.last_state_change > self.config.timeout:
                self._transition_to_half_open()
            return True

        return False

    def record_success(self):
        """Record a successful request."""
        self.total_requests += 1
        self.total_successes += 1

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count after successful requests
            if self.failure_count > 0 and time.time() - self.last_failure_time > self.config.reset_timeout:
                self.failure_count = 0

    def record_failure(self):
        """Record a failed request."""
        self.total_requests += 1
        self.total_failures += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state immediately opens circuit
            self._transition_to_open()

    def _transition_to_open(self):
        """Transition circuit to open state."""
        if self.state != CircuitState.OPEN:
            logger.warning(f"Circuit breaker '{self.name}' transitioning to OPEN state")
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            self.circuit_opens += 1
            self.success_count = 0

    def _transition_to_closed(self):
        """Transition circuit to closed state."""
        if self.state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED state")
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            self.failure_count = 0
            self.success_count = 0

    def _transition_to_half_open(self):
        """Transition circuit to half-open state."""
        if self.state != CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN state")
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = time.time()
            self.success_count = 0

    def can_make_request(self) -> bool:
        """Check if a request can be made in the current state."""
        if self.state == CircuitState.OPEN:
            return False
        elif self.state == CircuitState.HALF_OPEN:
            # Limit requests in half-open state
            return self.success_count < self.config.half_open_max_requests
        else:  # CLOSED
            return True

    def get_state_info(self) -> dict:
        """Get current state information."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_state_change": self.last_state_change,
            "time_in_state": time.time() - self.last_state_change,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "circuit_opens": self.circuit_opens,
            "failure_rate": (self.total_failures / self.total_requests * 100) if self.total_requests > 0 else 0
        }

    def reset(self):
        """Reset circuit breaker to initial state."""
        logger.info(f"Circuit breaker '{self.name}' reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.circuit_opens = 0


class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""

    def __init__(self):
        self.circuits: dict[str, CircuitBreaker] = {}

    def get_circuit(self, name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self.circuits:
            self.circuits[name] = CircuitBreaker(name, config)
        return self.circuits[name]

    def record_success(self, name: str):
        """Record success for a circuit breaker."""
        if name in self.circuits:
            self.circuits[name].record_success()

    def record_failure(self, name: str):
        """Record failure for a circuit breaker."""
        if name in self.circuits:
            self.circuits[name].record_failure()

    def is_circuit_open(self, name: str) -> bool:
        """Check if a circuit breaker is open."""
        if name in self.circuits:
            return self.circuits[name].is_open()
        return False

    def get_all_state_info(self) -> dict:
        """Get state information for all circuit breakers."""
        return {name: circuit.get_state_info() for name, circuit in self.circuits.items()}

    def reset_circuit(self, name: str):
        """Reset a specific circuit breaker."""
        if name in self.circuits:
            self.circuits[name].reset()

    def reset_all(self):
        """Reset all circuit breakers."""
        for circuit in self.circuits.values():
            circuit.reset()


def circuit_breaker_decorator(circuit_name: str, config: CircuitBreakerConfig | None = None):
    """Decorator for applying circuit breaker pattern to functions."""

    def decorator(func: Callable):
        circuit = CircuitBreaker(circuit_name, config)

        def wrapper(*args, **kwargs):
            if circuit.is_open():
                raise CircuitBreakerError(f"Circuit breaker '{circuit_name}' is open")

            try:
                result = func(*args, **kwargs)
                circuit.record_success()
                return result
            except Exception:
                circuit.record_failure()
                raise

        return wrapper

    return decorator


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()


# Predefined circuit breaker configurations for common external services
EXTERNAL_SERVICE_CONFIGS = {
    "google_search": CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=30,
        reset_timeout=180
    ),
    "semantic_scholar": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout=60,
        reset_timeout=300
    ),
    "news_api": CircuitBreakerConfig(
        failure_threshold=4,
        success_threshold=2,
        timeout=45,
        reset_timeout=240
    ),
    "ai_service": CircuitBreakerConfig(
        failure_threshold=2,  # More sensitive to AI service failures
        success_threshold=1,
        timeout=90,
        reset_timeout=360
    )
}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get a circuit breaker for a specific external service."""
    config = EXTERNAL_SERVICE_CONFIGS.get(service_name, CircuitBreakerConfig())
    return circuit_breaker_manager.get_circuit(service_name, config)
