"""Comprehensive tests for the LLM abstraction layer implementation."""

import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.config.llm import OllamaConfig, OpenAIConfig
from src.config.llm_config import LLMConfigManager, get_llm_config_manager
from src.services.llm.base import LLMProvider
from src.services.llm.error_handler import CircuitBreaker, ErrorHandler, MultiProviderErrorHandler
from src.services.llm.factory import (
    LLMProviderFactory,
    ProviderInstance,
    ProviderLifecycleState,
    get_llm_provider_factory,
    shutdown_all_providers,
)
from src.services.llm.health_monitor import HealthMonitor, HealthCheckResult, HealthStatus, get_health_monitor
from src.services.llm.ollama_provider import OllamaProvider


@pytest.fixture
def mock_ollama_config():
    """Fixture for mock Ollama configuration."""
    return OllamaConfig(
        provider_type="ollama",
        base_url="http://localhost:11434",
        model_name="llama2",
        temperature=0.7,
        max_tokens=1000,
        timeout=30,
        max_retries=3,
        context_window=4096,
        stream=False
    )


@pytest.fixture
def mock_openai_config():
    """Fixture for mock OpenAI configuration."""
    return OpenAIConfig(
        provider_type="openai",
        base_url="https://api.openai.com/v1",
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=1000,
        timeout=30,
        max_retries=3,
        api_key="test-key",
        organization="test-org"
    )


@pytest.fixture
def mock_ollama_provider(mock_ollama_config):
    """Fixture for mock Ollama provider."""
    provider = OllamaProvider(mock_ollama_config)
    provider.generate = AsyncMock(return_value="Test response")
    provider.generate_stream = AsyncMock(return_value=["Test", "response", "stream"])
    provider.health_check = AsyncMock(return_value=True)
    return provider


@pytest.mark.asyncio
class TestLLMConfigManager:
    """Test suite for LLMConfigManager."""
    
    async def test_singleton_pattern(self):
        """Test that LLMConfigManager follows singleton pattern."""
        manager1 = get_llm_config_manager()
        manager2 = get_llm_config_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, LLMConfigManager)
    
    async def test_load_environment_config(self):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, {
            "LLM_DEFAULT_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://test:11434",
            "OLLAMA_MODEL_NAME": "test-model",
            "OLLAMA_TIMEOUT": "60",
            "OLLAMA_MAX_RETRIES": "5"
        }):
            manager = get_llm_config_manager()
            config = manager.get_provider_config("ollama")
            
            assert config is not None
            assert config.base_url == "http://test:11434"
            assert config.model_name == "test-model"
            assert config.timeout == 60
            assert config.max_retries == 5
    
    async def test_get_default_provider(self):
        """Test getting default provider configuration."""
        with patch.dict(os.environ, {
            "LLM_DEFAULT_PROVIDER": "ollama"
        }):
            manager = get_llm_config_manager()
            default_config = manager.get_default_provider()
            
            assert default_config is not None
            assert default_config.provider_type == "ollama"
    
    async def test_to_provider_config(self, mock_ollama_config):
        """Test converting environment config to provider config."""
        manager = get_llm_config_manager()
        
        # Create a mock environment config
        env_config = MagicMock()
        env_config.provider_type = "ollama"
        env_config.base_url = "http://test:11434"
        env_config.model_name = "test-model"
        env_config.temperature = 0.7
        env_config.max_tokens = 1000
        env_config.timeout = 30
        env_config.max_retries = 3
        env_config.context_window = 4096
        env_config.stream = False
        
        provider_config = manager.to_provider_config(env_config)
        
        assert isinstance(provider_config, OllamaConfig)
        assert provider_config.base_url == "http://test:11434"
        assert provider_config.model_name == "test-model"
    
    async def test_config_validation(self):
        """Test configuration validation."""
        with patch.dict(os.environ, {
            "OLLAMA_BASE_URL": "invalid-url",
            "OLLAMA_TIMEOUT": "-10"
        }):
            manager = get_llm_config_manager()
            
            # Should handle invalid configurations gracefully
            config = manager.get_provider_config("ollama")
            assert config is not None  # Should return default config


@pytest.mark.asyncio
class TestCircuitBreaker:
    """Test suite for CircuitBreaker."""
    
    async def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state."""
        cb = CircuitBreaker("test-provider")
        
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
    
    async def test_circuit_breaker_trip(self):
        """Test circuit breaker tripping."""
        cb = CircuitBreaker("test-provider")
        
        # Trip the circuit breaker
        for _ in range(5):
            cb.record_failure()
        
        assert cb.state == "OPEN"
        assert cb.failure_count == 5
    
    async def test_circuit_breaker_reset(self):
        """Test circuit breaker reset."""
        cb = CircuitBreaker("test-provider")
        
        # Trip the circuit breaker
        for _ in range(5):
            cb.record_failure()
        
        # Reset
        cb.record_success()
        
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
    
    async def test_circuit_breaker_half_open(self):
        """Test circuit breaker half-open state."""
        cb = CircuitBreaker("test-provider")
        
        # Trip the circuit breaker
        for _ in range(5):
            cb.record_failure()
        
        # Wait for reset timeout
        cb.last_failure_time = time.time() - cb.reset_timeout - 1
        
        assert cb.state == "HALF_OPEN"
    
    async def test_can_execute(self):
        """Test can_execute method."""
        cb = CircuitBreaker("test-provider")
        
        # Initially should be able to execute
        assert cb.can_execute() is True
        
        # Trip the circuit breaker
        for _ in range(5):
            cb.record_failure()
        
        # Should not be able to execute
        assert cb.can_execute() is False


@pytest.mark.asyncio
class TestErrorHandler:
    """Test suite for ErrorHandler."""
    
    async def test_error_handler_initialization(self):
        """Test error handler initialization."""
        cb = CircuitBreaker("test-provider")
        handler = ErrorHandler(cb)
        
        assert handler.circuit_breaker is cb
        assert handler.retry_strategy is not None
    
    async def test_handle_operation_success(self):
        """Test handling successful operation."""
        cb = CircuitBreaker("test-provider")
        handler = ErrorHandler(cb)
        
        async def successful_operation():
            return "success"
        
        result = await handler.handle_operation(successful_operation)
        
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"
    
    async def test_handle_operation_failure(self):
        """Test handling failed operation."""
        cb = CircuitBreaker("test-provider")
        handler = ErrorHandler(cb)
        
        async def failing_operation():
            raise Exception("Test failure")
        
        with pytest.raises(Exception):
            await handler.handle_operation(failing_operation)
        
        assert cb.failure_count == 1
    
    async def test_handle_operation_with_retry(self):
        """Test handling operation with retry."""
        cb = CircuitBreaker("test-provider")
        handler = ErrorHandler(cb)
        
        call_count = 0
        
        async def eventually_successful_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = await handler.handle_operation(eventually_successful_operation, max_retries=3)
        
        assert result == "success"
        assert call_count == 2


@pytest.mark.asyncio
class TestHealthMonitor:
    """Test suite for HealthMonitor."""
    
    async def test_health_monitor_singleton(self):
        """Test health monitor singleton pattern."""
        monitor1 = get_health_monitor()
        monitor2 = get_health_monitor()
        
        assert monitor1 is monitor2
        assert isinstance(monitor1, HealthMonitor)
    
    async def test_register_provider(self, mock_ollama_provider):
        """Test registering a provider."""
        monitor = get_health_monitor()
        cb = CircuitBreaker("test-provider")
        
        monitor.register_provider("test-provider", mock_ollama_provider, cb)
        
        assert "test-provider" in monitor._providers
        assert monitor._providers["test-provider"]["instance"] is mock_ollama_provider
        assert monitor._providers["test-provider"]["circuit_breaker"] is cb
    
    async def test_health_check_success(self, mock_ollama_provider):
        """Test successful health check."""
        monitor = get_health_monitor()
        cb = CircuitBreaker("test-provider")
        
        mock_ollama_provider.health_check = AsyncMock(return_value=True)
        monitor.register_provider("test-provider", mock_ollama_provider, cb)
        
        result = await monitor.force_health_check("test-provider")
        
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time > 0
        assert result.timestamp is not None
    
    async def test_health_check_failure(self, mock_ollama_provider):
        """Test failed health check."""
        monitor = get_health_monitor()
        cb = CircuitBreaker("test-provider")
        
        mock_ollama_provider.health_check = AsyncMock(side_effect=Exception("Health check failed"))
        monitor.register_provider("test-provider", mock_ollama_provider, cb)
        
        result = await monitor.force_health_check("test-provider")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert result.error == "Health check failed"
    
    async def test_get_healthy_providers(self, mock_ollama_provider):
        """Test getting healthy providers."""
        monitor = get_health_monitor()
        cb = CircuitBreaker("test-provider")
        
        mock_ollama_provider.health_check = AsyncMock(return_value=True)
        monitor.register_provider("test-provider", mock_ollama_provider, cb)
        
        # Force a health check to update status
        await monitor.force_health_check("test-provider")
        
        healthy_providers = monitor.get_healthy_providers()
        
        assert "test-provider" in healthy_providers
        assert healthy_providers["test-provider"].status == HealthStatus.HEALTHY


@pytest.mark.asyncio
class TestLLMProviderFactory:
    """Test suite for LLMProviderFactory."""
    
    async def test_factory_singleton(self):
        """Test factory singleton pattern."""
        factory1 = get_llm_provider_factory()
        factory2 = get_llm_provider_factory()
        
        assert factory1 is factory2
        assert isinstance(factory1, LLMProviderFactory)
    
    async def test_create_provider(self, mock_ollama_config):
        """Test creating a provider instance."""
        factory = get_llm_provider_factory()
        
        provider_instance = await factory.create_provider(mock_ollama_config, "test-provider")
        
        assert isinstance(provider_instance, ProviderInstance)
        assert provider_instance.provider_name == "test-provider"
        assert provider_instance.provider_type == "ollama"
        assert provider_instance.state == ProviderLifecycleState.ACTIVE
    
    async def test_create_from_environment(self):
        """Test creating provider from environment configuration."""
        with patch.dict(os.environ, {
            "OLLAMA_BASE_URL": "http://test:11434",
            "OLLAMA_MODEL_NAME": "test-model"
        }):
            factory = get_llm_provider_factory()
            
            provider_instance = await factory.create_from_environment("ollama", "test-env-provider")
            
            assert isinstance(provider_instance, ProviderInstance)
            assert provider_instance.provider_name == "test-env-provider"
            assert provider_instance.provider_type == "ollama"
    
    async def test_get_provider(self, mock_ollama_config):
        """Test getting a provider instance."""
        factory = get_llm_provider_factory()
        
        # Create a provider
        await factory.create_provider(mock_ollama_config, "test-provider")
        
        # Get the provider
        provider_instance = await factory.get_provider("test-provider")
        
        assert provider_instance is not None
        assert provider_instance.provider_name == "test-provider"
    
    async def test_get_active_providers(self, mock_ollama_config):
        """Test getting active providers."""
        factory = get_llm_provider_factory()
        
        # Create a provider
        await factory.create_provider(mock_ollama_config, "test-provider")
        
        active_providers = await factory.get_active_providers()
        
        assert len(active_providers) > 0
        assert any(p.provider_name == "test-provider" for p in active_providers)
    
    async def test_shutdown_provider(self, mock_ollama_config):
        """Test shutting down a provider."""
        factory = get_llm_provider_factory()
        
        # Create a provider
        await factory.create_provider(mock_ollama_config, "test-provider")
        
        # Shutdown the provider
        await factory.shutdown_provider("test-provider")
        
        # Verify provider is gone
        provider_instance = await factory.get_provider("test-provider")
        assert provider_instance is None
    
    async def test_register_provider_type(self):
        """Test registering a new provider type."""
        factory = get_llm_provider_factory()
        
        class TestProvider(LLMProvider):
            def __init__(self, config):
                super().__init__(config)
            
            async def generate(self, prompt, **kwargs):
                return "Test response"
            
            async def generate_stream(self, prompt, **kwargs):
                return ["Test", "response"]
            
            async def health_check(self):
                return True
        
        # Register the new provider type
        LLMProviderFactory.register_provider_type("test", TestProvider)
        
        # Verify registration
        available_types = LLMProviderFactory.get_available_provider_types()
        assert "test" in available_types
        assert available_types["test"] is TestProvider


@pytest.mark.asyncio
class TestProviderInstance:
    """Test suite for ProviderInstance."""
    
    async def test_provider_instance_creation(self, mock_ollama_config, mock_ollama_provider):
        """Test provider instance creation."""
        instance = ProviderInstance(
            provider_name="test-instance",
            provider_type="ollama",
            provider_instance=mock_ollama_provider,
            config=mock_ollama_config
        )
        
        assert instance.provider_name == "test-instance"
        assert instance.provider_type == "ollama"
        assert instance.provider_instance is mock_ollama_provider
        assert instance.config is mock_ollama_config
        assert instance.state == ProviderLifecycleState.CREATED
        assert instance.constitutional_audit is not None
    
    async def test_initialize(self, mock_ollama_config, mock_ollama_provider):
        """Test provider instance initialization."""
        instance = ProviderInstance(
            provider_name="test-instance",
            provider_type="ollama",
            provider_instance=mock_ollama_provider,
            config=mock_ollama_config
        )
        
        await instance.initialize()
        
        assert instance.state == ProviderLifecycleState.INITIALIZED
        assert instance.circuit_breaker is not None
        assert instance.error_handler is not None
        assert "initialized_at" in instance.constitutional_audit
    
    async def test_activate(self, mock_ollama_config, mock_ollama_provider):
        """Test provider instance activation."""
        instance = ProviderInstance(
            provider_name="test-instance",
            provider_type="ollama",
            provider_instance=mock_ollama_provider,
            config=mock_ollama_config
        )
        
        await instance.initialize()
        await instance.activate()
        
        assert instance.state in [ProviderLifecycleState.ACTIVE, ProviderLifecycleState.DEGRADED, ProviderLifecycleState.UNHEALTHY]
        assert instance.last_health_check is not None
        assert "activated_at" in instance.constitutional_audit
    
    async def test_shutdown(self, mock_ollama_config, mock_ollama_provider):
        """Test provider instance shutdown."""
        instance = ProviderInstance(
            provider_name="test-instance",
            provider_type="ollama",
            provider_instance=mock_ollama_provider,
            config=mock_ollama_config
        )
        
        await instance.initialize()
        await instance.activate()
        await instance.shutdown()
        
        assert instance.state == ProviderLifecycleState.SHUTDOWN
        assert "shutdown_at" in instance.constitutional_audit


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the complete LLM abstraction layer."""
    
    async def test_complete_workflow(self, mock_ollama_config):
        """Test complete workflow from configuration to provider usage."""
        # Get the factory
        factory = get_llm_provider_factory()
        
        # Create a provider
        provider_instance = await factory.create_provider(mock_ollama_config, "integration-test")
        
        # Verify provider is active
        assert provider_instance.state == ProviderLifecycleState.ACTIVE
        
        # Get the health monitor
        monitor = get_health_monitor()
        
        # Check provider health
        health_result = await monitor.force_health_check("integration-test")
        assert health_result.status == HealthStatus.HEALTHY
        
        # Get factory status
        status = await factory.get_factory_status()
        assert status["total_managed_instances"] > 0
        assert "integration-test" in status["instances"]
        
        # Cleanup
        await factory.shutdown_provider("integration-test")
    
    async def test_multi_provider_fallback(self, mock_ollama_config):
        """Test multi-provider fallback scenario."""
        factory = get_llm_provider_factory()
        
        # Create multiple providers
        provider1 = await factory.create_provider(mock_ollama_config, "provider-1")
        provider2 = await factory.create_provider(mock_ollama_config, "provider-2")
        
        # Get healthy providers
        healthy_providers = await factory.get_healthy_providers()
        assert len(healthy_providers) >= 2
        
        # Simulate provider failure
        provider1.provider_instance.health_check = AsyncMock(return_value=False)
        
        # Refresh health
        await factory.refresh_provider_health("provider-1")
        
        # Verify provider-1 is now unhealthy
        updated_provider1 = await factory.get_provider("provider-1")
        assert updated_provider1.state == ProviderLifecycleState.UNHEALTHY
        
        # Provider-2 should still be healthy
        updated_provider2 = await factory.get_provider("provider-2")
        assert updated_provider2.state == ProviderLifecycleState.ACTIVE
        
        # Cleanup
        await factory.shutdown_provider("provider-1")
        await factory.shutdown_provider("provider-2")
    
    async def test_constitutional_compliance(self, mock_ollama_config):
        """Test constitutional compliance features."""
        factory = get_llm_provider_factory()
        
        # Create a provider
        provider_instance = await factory.create_provider(mock_ollama_config, "compliance-test")
        
        # Verify constitutional audit trail
        audit_trail = provider_instance.constitutional_audit
        assert audit_trail is not None
        assert "created_at" in audit_trail
        assert "initialized_at" in audit_trail
        assert "activated_at" in audit_trail
        assert "initial_health_status" in audit_trail
        
        # Cleanup
        await factory.shutdown_provider("compliance-test")


@pytest.mark.asyncio
class TestErrorScenarios:
    """Test error scenarios and edge cases."""
    
    async def test_provider_not_found(self):
        """Test handling of non-existent provider."""
        factory = get_llm_provider_factory()
        
        provider_instance = await factory.get_provider("non-existent")
        assert provider_instance is None
    
    async def test_invalid_provider_type(self):
        """Test handling of invalid provider type."""
        factory = get_llm_provider_factory()
        
        with pytest.raises(ValueError):
            await factory.create_from_environment("invalid-type", "test-provider")
    
    async def test_duplicate_provider_name(self, mock_ollama_config):
        """Test handling of duplicate provider names."""
        factory = get_llm_provider_factory()
        
        # Create first provider
        await factory.create_provider(mock_ollama_config, "duplicate-test")
        
        # Try to create another with same name
        with pytest.raises(ValueError):
            await factory.create_provider(mock_ollama_config, "duplicate-test")
        
        # Cleanup
        await factory.shutdown_provider("duplicate-test")
    
    async def test_circuit_breaker_recovery(self, mock_ollama_config):
        """Test circuit breaker recovery after timeout."""
        factory = get_llm_provider_factory()
        
        # Create a provider
        provider_instance = await factory.create_provider(mock_ollama_config, "recovery-test")
        
        # Simulate multiple failures to trip circuit breaker
        cb = provider_instance.circuit_breaker
        for _ in range(10):
            cb.record_failure()
        
        assert cb.state == "OPEN"
        
        # Wait for reset timeout
        cb.last_failure_time = time.time() - cb.reset_timeout - 1
        
        # Should be in half-open state now
        assert cb.state == "HALF_OPEN"
        
        # Record success to close circuit
        cb.record_success()
        assert cb.state == "CLOSED"
        
        # Cleanup
        await factory.shutdown_provider("recovery-test")


@pytest.fixture(scope="function", autouse=True)
async def cleanup_providers():
    """Cleanup function to shutdown all providers after each test."""
    yield
    await shutdown_all_providers()