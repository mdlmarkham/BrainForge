"""Enhanced factory pattern for LLM provider instantiation with lifecycle management."""

import asyncio
import time
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import Field

from src.config.llm import LLMProviderConfig, OllamaConfig
from src.config.llm_config import get_llm_config_manager
from src.models.base import BrainForgeBaseModel, TimestampMixin
from src.services.llm.base import LLMProvider
from src.services.llm.error_handler import CircuitBreaker, ErrorHandler
from src.services.llm.health_monitor import HealthStatus, get_health_monitor
from src.services.llm.ollama_provider import OllamaProvider


class ProviderLifecycleState(Enum):
    """Lifecycle states for provider instances."""
    CREATED = "created"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SHUTDOWN = "shutdown"


class ProviderInstance(BrainForgeBaseModel, TimestampMixin):
    """Managed provider instance with lifecycle tracking."""

    id: UUID = Field(default_factory=uuid4)
    provider_name: str = Field(..., description="Name of the provider")
    provider_type: str = Field(..., description="Type of provider")
    provider_instance: LLMProvider = Field(..., description="Actual provider instance")
    state: ProviderLifecycleState = Field(ProviderLifecycleState.CREATED, description="Current lifecycle state")
    config: LLMProviderConfig = Field(..., description="Provider configuration")
    circuit_breaker: CircuitBreaker | None = Field(None, description="Circuit breaker instance")
    error_handler: ErrorHandler | None = Field(None, description="Error handler instance")
    last_health_check: float | None = Field(None, description="Timestamp of last health check")
    constitutional_audit: dict[str, Any] = Field(default_factory=dict)

    async def initialize(self) -> None:
        """Initialize the provider instance."""
        if self.state != ProviderLifecycleState.CREATED:
            raise ValueError(f"Cannot initialize provider in state: {self.state}")

        # Initialize circuit breaker and error handler
        self.circuit_breaker = CircuitBreaker(self.provider_name)
        self.error_handler = ErrorHandler(self.circuit_breaker)

        # Register with health monitor
        health_monitor = get_health_monitor()
        health_monitor.register_provider(self.provider_name, self.provider_instance, self.circuit_breaker)

        self.state = ProviderLifecycleState.INITIALIZED
        self.constitutional_audit.update({
            "initialized_at": time.time(),
            "circuit_breaker_created": True,
            "health_monitor_registered": True
        })

    async def activate(self) -> None:
        """Activate the provider instance."""
        if self.state != ProviderLifecycleState.INITIALIZED:
            raise ValueError(f"Cannot activate provider in state: {self.state}")

        # Perform initial health check
        health_monitor = get_health_monitor()
        health_result = await health_monitor.force_health_check(self.provider_name)

        if health_result.status == HealthStatus.HEALTHY:
            self.state = ProviderLifecycleState.ACTIVE
        elif health_result.status == HealthStatus.DEGRADED:
            self.state = ProviderLifecycleState.DEGRADED
        else:
            self.state = ProviderLifecycleState.UNHEALTHY

        self.last_health_check = time.time()
        self.constitutional_audit.update({
            "activated_at": time.time(),
            "initial_health_status": health_result.status.value
        })

    async def shutdown(self) -> None:
        """Shutdown the provider instance."""
        if self.state == ProviderLifecycleState.SHUTDOWN:
            return

        # Cleanup resources if needed
        if hasattr(self.provider_instance, 'close'):
            await self.provider_instance.close()

        self.state = ProviderLifecycleState.SHUTDOWN
        self.constitutional_audit.update({
            "shutdown_at": time.time(),
            "resources_cleaned": True
        })


class LLMProviderFactory:
    """Enhanced factory for creating and managing LLM provider instances."""

    _instance: Optional["LLMProviderFactory"] = None
    _provider_registry: dict[str, type[LLMProvider]] = {
        "ollama": OllamaProvider,
        # "openai": OpenAIConfig,  # Will be implemented later
    }
    _managed_instances: dict[str, ProviderInstance] = {}
    _config_manager = get_llm_config_manager()
    _health_monitor = get_health_monitor()

    def __new__(cls) -> "LLMProviderFactory":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize factory with lifecycle management."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._lock = asyncio.Lock()

    async def create_provider(self, config: LLMProviderConfig,
                            provider_name: str | None = None) -> ProviderInstance:
        """Create and manage a provider instance with full lifecycle support.
        
        Args:
            config: Provider configuration
            provider_name: Optional custom name for the provider instance
            
        Returns:
            Managed ProviderInstance
        """
        provider_name = provider_name or f"{config.provider_type}_{uuid4().hex[:8]}"

        async with self._lock:
            if provider_name in self._managed_instances:
                raise ValueError(f"Provider instance already exists: {provider_name}")

            # Create provider instance
            provider_class = self._provider_registry.get(config.provider_type)
            if not provider_class:
                raise ValueError(f"Unsupported provider type: {config.provider_type}")

            provider_instance = provider_class(config)

            # Create managed instance
            managed_instance = ProviderInstance(
                provider_name=provider_name,
                provider_type=config.provider_type,
                provider_instance=provider_instance,
                config=config
            )

            # Initialize and activate
            await managed_instance.initialize()
            await managed_instance.activate()

            self._managed_instances[provider_name] = managed_instance

            return managed_instance

    async def create_from_environment(self, provider_type: str,
                                    provider_name: str | None = None) -> ProviderInstance:
        """Create provider from environment configuration.
        
        Args:
            provider_type: Type of provider to create
            provider_name: Optional custom name for the provider instance
            
        Returns:
            Managed ProviderInstance
        """
        env_config = self._config_manager.get_provider_config(provider_type)
        if not env_config:
            raise ValueError(f"Provider configuration not found: {provider_type}")

        provider_config = self._config_manager.to_provider_config(env_config)
        return await self.create_provider(provider_config, provider_name)

    async def create_default_provider(self) -> ProviderInstance:
        """Create the default provider based on environment configuration."""
        default_config = self._config_manager.get_default_provider()
        if not default_config:
            raise ValueError("No default provider configuration found")

        provider_config = self._config_manager.to_provider_config(default_config)
        return await self.create_provider(provider_config, "default_provider")

    async def get_provider(self, provider_name: str) -> ProviderInstance | None:
        """Get a managed provider instance by name."""
        return self._managed_instances.get(provider_name)

    async def get_active_providers(self) -> list[ProviderInstance]:
        """Get list of active provider instances."""
        return [
            instance for instance in self._managed_instances.values()
            if instance.state in [ProviderLifecycleState.ACTIVE, ProviderLifecycleState.DEGRADED]
        ]

    async def get_healthy_providers(self) -> list[ProviderInstance]:
        """Get list of healthy provider instances."""
        return [
            instance for instance in self._managed_instances.values()
            if instance.state == ProviderLifecycleState.ACTIVE
        ]

    async def shutdown_provider(self, provider_name: str) -> None:
        """Shutdown a specific provider instance."""
        async with self._lock:
            instance = self._managed_instances.get(provider_name)
            if instance:
                await instance.shutdown()
                del self._managed_instances[provider_name]

    async def shutdown_all(self) -> None:
        """Shutdown all managed provider instances."""
        async with self._lock:
            for instance in list(self._managed_instances.values()):
                await instance.shutdown()
            self._managed_instances.clear()

    async def refresh_provider_health(self, provider_name: str) -> ProviderInstance:
        """Refresh health status for a provider instance."""
        instance = self._managed_instances.get(provider_name)
        if not instance:
            raise ValueError(f"Provider instance not found: {provider_name}")

        health_result = await self._health_monitor.force_health_check(provider_name)
        instance.last_health_check = time.time()

        if health_result.status == HealthStatus.HEALTHY:
            instance.state = ProviderLifecycleState.ACTIVE
        elif health_result.status == HealthStatus.DEGRADED:
            instance.state = ProviderLifecycleState.DEGRADED
        else:
            instance.state = ProviderLifecycleState.UNHEALTHY

        return instance

    @classmethod
    def register_provider_type(cls, provider_type: str, provider_class: type[LLMProvider]) -> None:
        """Register a new provider type.
        
        Args:
            provider_type: Type identifier for the provider
            provider_class: Provider class implementation
        """
        if not issubclass(provider_class, LLMProvider):
            raise ValueError("Provider class must inherit from LLMProvider")

        cls._provider_registry[provider_type] = provider_class

    @classmethod
    def get_available_provider_types(cls) -> dict[str, type[LLMProvider]]:
        """Get dictionary of available provider types and their classes."""
        return cls._provider_registry.copy()

    async def get_factory_status(self) -> dict[str, Any]:
        """Get comprehensive status of the factory and managed instances."""
        active_count = len(await self.get_active_providers())
        healthy_count = len(await self.get_healthy_providers())
        total_count = len(self._managed_instances)

        return {
            "total_managed_instances": total_count,
            "active_instances": active_count,
            "healthy_instances": healthy_count,
            "available_provider_types": list(self._provider_registry.keys()),
            "instances": {
                name: {
                    "state": instance.state.value,
                    "provider_type": instance.provider_type,
                    "last_health_check": instance.last_health_check
                }
                for name, instance in self._managed_instances.items()
            }
        }


# Global factory instance
_factory = LLMProviderFactory()


def get_llm_provider_factory() -> LLMProviderFactory:
    """Get the global LLM provider factory instance."""
    return _factory


async def create_managed_provider(
    provider_type: str = "ollama",
    provider_name: str | None = None,
    **kwargs
) -> ProviderInstance:
    """Convenience function to create a managed LLM provider.
    
    Args:
        provider_type: Type of provider to create
        provider_name: Optional custom name for the provider instance
        **kwargs: Additional configuration parameters
        
    Returns:
        Managed ProviderInstance
    """
    factory = get_llm_provider_factory()

    if provider_name and await factory.get_provider(provider_name):
        raise ValueError(f"Provider instance already exists: {provider_name}")

    # Create settings from kwargs
    settings = {
        "provider_type": provider_type,
        **kwargs
    }

    # Use environment configuration as base
    config_manager = get_llm_config_manager()
    env_config = config_manager.get_provider_config(provider_type)

    if env_config:
        # Override with provided kwargs
        for key, value in kwargs.items():
            if hasattr(env_config, key):
                setattr(env_config, key, value)

        provider_config = config_manager.to_provider_config(env_config)
    else:
        # Fallback to direct configuration
        if provider_type == "ollama":
            provider_config = OllamaConfig(
                provider_type=provider_type,
                base_url=kwargs.get("base_url", "http://localhost:11434"),
                model_name=kwargs.get("model_name", "llama2"),
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens"),
                timeout=kwargs.get("timeout", 30),
                max_retries=kwargs.get("max_retries", 3),
                context_window=kwargs.get("context_window"),
                stream=kwargs.get("stream", False)
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

    return await factory.create_provider(provider_config, provider_name)


async def create_llm_provider(
    provider_type: str = "ollama",
    provider_name: str | None = None,
    **kwargs
) -> LLMProvider:
    """Convenience function to create an LLM provider instance.
    
    This function provides a simplified interface for creating LLM providers
    without the full lifecycle management of create_managed_provider.
    
    Args:
        provider_type: Type of provider to create
        provider_name: Optional custom name for the provider instance
        **kwargs: Additional configuration parameters
        
    Returns:
        LLMProvider instance
    """
    managed_instance = await create_managed_provider(provider_type, provider_name, **kwargs)
    return managed_instance.provider_instance


async def shutdown_all_providers() -> None:
    """Shutdown all managed provider instances."""
    factory = get_llm_provider_factory()
    await factory.shutdown_all()
