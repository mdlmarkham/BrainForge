"""Health monitoring system for LLM providers."""

import asyncio
import time
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.base import BrainForgeBaseModel, ProvenanceMixin, TimestampMixin
from src.services.llm.base import LLMProvider
from src.services.llm.error_handler import CircuitBreaker


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult(BrainForgeBaseModel, TimestampMixin):
    """Result of a health check."""
    
    id: UUID = Field(default_factory=uuid4)
    provider_name: str = Field(..., description="Name of the provider being checked")
    status: HealthStatus = Field(..., description="Health status")
    response_time: Optional[float] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if check failed")
    error: Optional[str] = Field(None, description="Error message (alias for error_message)")
    timestamp: float = Field(default_factory=time.time, description="Timestamp of the health check")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    constitutional_audit: Dict[str, Any] = Field(default_factory=dict)


class HealthMetrics(BrainForgeBaseModel, TimestampMixin):
    """Aggregated health metrics for a provider."""
    
    id: UUID = Field(default_factory=uuid4)
    provider_name: str = Field(..., description="Name of the provider")
    overall_status: HealthStatus = Field(..., description="Overall health status")
    availability_rate: float = Field(0.0, ge=0.0, le=1.0, description="Availability rate (0.0 to 1.0)")
    average_response_time: float = Field(0.0, ge=0.0, description="Average response time in milliseconds")
    total_checks: int = Field(0, description="Total number of health checks")
    successful_checks: int = Field(0, description="Number of successful checks")
    failed_checks: int = Field(0, description="Number of failed checks")
    last_check_time: Optional[float] = Field(None, description="Timestamp of last check")
    consecutive_failures: int = Field(0, description="Consecutive failures")
    constitutional_audit: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_checks == 0:
            return 0.0
        return self.successful_checks / self.total_checks


class HealthCheckConfig(BrainForgeBaseModel):
    """Configuration for health checks."""
    
    check_interval: int = Field(30, ge=1, description="Interval between checks (seconds)")
    timeout: int = Field(10, ge=1, description="Health check timeout (seconds)")
    failure_threshold: int = Field(3, ge=1, description="Consecutive failures before marking unhealthy")
    recovery_threshold: int = Field(2, ge=1, description="Consecutive successes before marking healthy")
    degraded_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Success rate threshold for degraded status")
    enabled: bool = Field(True, description="Enable health monitoring")


class HealthMonitor:
    """Health monitor for LLM providers."""
    
    def __init__(self, config: Optional[HealthCheckConfig] = None):
        """Initialize health monitor."""
        self.config = config or HealthCheckConfig()
        self._providers: Dict[str, Dict[str, Any]] = {}
        self._metrics: Dict[str, HealthMetrics] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    def register_provider(self, provider_name: str, provider: LLMProvider,
                         circuit_breaker: Optional[CircuitBreaker] = None) -> None:
        """Register a provider for health monitoring."""
        self._providers[provider_name] = {
            "instance": provider,
            "circuit_breaker": circuit_breaker
        }
        
        # Initialize metrics
        self._metrics[provider_name] = HealthMetrics(
            provider_name=provider_name,
            overall_status=HealthStatus.UNKNOWN,
            availability_rate=0.0,
            average_response_time=0.0,
            total_checks=0,
            successful_checks=0,
            failed_checks=0,
            consecutive_failures=0
        )
        
        # Store circuit breaker if provided
        if circuit_breaker:
            self._circuit_breakers[provider_name] = circuit_breaker
    
    async def check_provider_health(self, provider_name: str) -> HealthCheckResult:
        """Perform health check for a specific provider."""
        if provider_name not in self._providers:
            return HealthCheckResult(
                provider_name=provider_name,
                status=HealthStatus.UNKNOWN,
                error_message=f"Provider not registered: {provider_name}"
            )
        
        provider = self._providers[provider_name]["instance"]
        start_time = time.time()
        
        try:
            # Use circuit breaker if available
            if provider_name in self._circuit_breakers:
                circuit_breaker = self._circuit_breakers[provider_name]
                await circuit_breaker.execute(provider.health_check)
            elif self._providers[provider_name]["circuit_breaker"]:
                circuit_breaker = self._providers[provider_name]["circuit_breaker"]
                await circuit_breaker.execute(provider.health_check)
            else:
                # Execute with timeout
                await asyncio.wait_for(provider.health_check(), timeout=self.config.timeout)
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            result = HealthCheckResult(
                provider_name=provider_name,
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                details={"check_type": "basic_health_check"}
            )
            
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                provider_name=provider_name,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                error_message="Health check timeout",
                details={"check_type": "basic_health_check", "timeout": self.config.timeout}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                provider_name=provider_name,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                error_message=str(e),
                details={"check_type": "basic_health_check", "error_type": type(e).__name__}
            )
        
        # Update constitutional audit
        result.constitutional_audit.update({
            "check_timestamp": start_time,
            "response_time_ms": result.response_time,
            "status_determined": True
        })
        
        await self._update_metrics(provider_name, result)
        return result
    
    async def _update_metrics(self, provider_name: str, result: HealthCheckResult) -> None:
        """Update health metrics based on check result."""
        async with self._lock:
            metrics = self._metrics[provider_name]
            metrics.total_checks += 1
            metrics.last_check_time = time.time()
            
            if result.status == HealthStatus.HEALTHY:
                metrics.successful_checks += 1
                metrics.consecutive_failures = 0
                
                # Update average response time
                if result.response_time:
                    if metrics.average_response_time == 0:
                        metrics.average_response_time = result.response_time
                    else:
                        metrics.average_response_time = (
                            (metrics.average_response_time * (metrics.successful_checks - 1) + 
                             result.response_time) / metrics.successful_checks
                        )
            else:
                metrics.failed_checks += 1
                metrics.consecutive_failures += 1
            
            # Update overall status
            metrics.availability_rate = metrics.successful_checks / metrics.total_checks
            
            if metrics.consecutive_failures >= self.config.failure_threshold:
                metrics.overall_status = HealthStatus.UNHEALTHY
            elif metrics.availability_rate < self.config.degraded_threshold:
                metrics.overall_status = HealthStatus.DEGRADED
            elif metrics.consecutive_failures == 0 and metrics.successful_checks >= self.config.recovery_threshold:
                metrics.overall_status = HealthStatus.HEALTHY
            else:
                metrics.overall_status = HealthStatus.DEGRADED  # Default to degraded during transition
            
            # Update constitutional audit
            metrics.constitutional_audit.update({
                "last_updated": time.time(),
                "availability_calculated": True,
                "status_reason": f"consecutive_failures={metrics.consecutive_failures}, "
                               f"availability_rate={metrics.availability_rate:.3f}"
            })
    
    async def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Check all registered providers
                for provider_name in list(self._providers.keys()):
                    await self.check_provider_health(provider_name)
                
                # Wait for next check interval
                await asyncio.sleep(self.config.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue monitoring
                print(f"Health monitoring error: {e}")
                await asyncio.sleep(self.config.check_interval)
    
    async def get_provider_health(self, provider_name: str) -> HealthMetrics:
        """Get health metrics for a specific provider."""
        if provider_name not in self._metrics:
            raise ValueError(f"Provider not monitored: {provider_name}")
        
        return self._metrics[provider_name]
    
    async def get_all_health_metrics(self) -> Dict[str, HealthMetrics]:
        """Get health metrics for all providers."""
        return self._metrics.copy()
    
    def get_healthy_providers(self) -> Dict[str, HealthStatus]:
        """Get all healthy providers with their status."""
        healthy_providers = {}
        
        for provider_name, provider_data in self._providers.items():
            metrics = self._metrics.get(provider_name)
            if metrics and metrics.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
                healthy_providers[provider_name] = metrics.overall_status
        
        return healthy_providers
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of health status across all providers."""
        total_providers = len(self._providers)
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        unknown_count = 0
        
        for metrics in self._metrics.values():
            if metrics.overall_status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif metrics.overall_status == HealthStatus.DEGRADED:
                degraded_count += 1
            elif metrics.overall_status == HealthStatus.UNHEALTHY:
                unhealthy_count += 1
            else:
                unknown_count += 1
        
        return {
            "total_providers": total_providers,
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
            "unknown": unknown_count,
            "overall_availability": healthy_count / total_providers if total_providers > 0 else 0.0,
            "timestamp": time.time()
        }
    
    async def force_health_check(self, provider_name: str) -> HealthCheckResult:
        """Force an immediate health check for a provider."""
        return await self.check_provider_health(provider_name)
    
    async def reset_metrics(self, provider_name: str) -> None:
        """Reset health metrics for a provider."""
        async with self._lock:
            if provider_name in self._metrics:
                self._metrics[provider_name] = HealthMetrics(
                    provider_name=provider_name,
                    overall_status=HealthStatus.UNKNOWN,
                    availability_rate=0.0,
                    average_response_time=0.0,
                    total_checks=0,
                    successful_checks=0,
                    failed_checks=0,
                    consecutive_failures=0
                )


class ProviderAvailabilityManager:
    """Manager for provider availability and selection."""
    
    def __init__(self, health_monitor: HealthMonitor):
        """Initialize availability manager."""
        self.health_monitor = health_monitor
    
    async def get_available_providers(self, min_availability: float = 0.7) -> List[str]:
        """Get list of available providers meeting minimum availability threshold."""
        metrics = await self.health_monitor.get_all_health_metrics()
        available_providers = []
        
        for provider_name, metric in metrics.items():
            if (metric.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED] and
                metric.availability_rate >= min_availability):
                available_providers.append(provider_name)
        
        return available_providers
    
    async def get_best_provider(self, preference_order: Optional[List[str]] = None) -> Optional[str]:
        """Get the best available provider based on health metrics."""
        if preference_order:
            # Try providers in preference order
            for provider_name in preference_order:
                if provider_name in self.health_monitor._metrics:
                    metrics = await self.health_monitor.get_provider_health(provider_name)
                    if (metrics.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED] and
                        metrics.availability_rate >= 0.5):  # Minimum 50% availability
                        return provider_name
        
        # Fallback: get provider with highest availability
        metrics = await self.health_monitor.get_all_health_metrics()
        best_provider = None
        best_availability = 0.0
        
        for provider_name, metric in metrics.items():
            if (metric.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED] and
                metric.availability_rate > best_availability):
                best_provider = provider_name
                best_availability = metric.availability_rate
        
        return best_provider
    
    async def is_provider_available(self, provider_name: str, min_availability: float = 0.5) -> bool:
        """Check if a specific provider is available."""
        try:
            metrics = await self.health_monitor.get_provider_health(provider_name)
            return (metrics.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED] and
                    metrics.availability_rate >= min_availability)
        except ValueError:
            return False


# Global health monitor instance
_health_monitor = HealthMonitor()


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    return _health_monitor


async def start_health_monitoring() -> None:
    """Start global health monitoring."""
    await _health_monitor.start_monitoring()


async def stop_health_monitoring() -> None:
    """Stop global health monitoring."""
    await _health_monitor.stop_monitoring()