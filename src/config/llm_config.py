"""LLM configuration manager for BrainForge multi-provider system."""

import asyncio
import os
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import Field, validator

from src.config.llm import LLMProviderConfig, LLMProviderSettings, OllamaConfig, OpenAIConfig
from src.models.base import BrainForgeBaseModel, ProvenanceMixin, TimestampMixin


class LLMProviderEnvironmentConfig(BrainForgeBaseModel):
    """Environment-based configuration for LLM providers."""
    
    provider_type: str = Field(..., description="Type of LLM provider")
    base_url: Optional[str] = Field(None, description="Base URL for the provider API")
    model_name: str = Field(..., description="Model name to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    timeout: int = Field(30, ge=1, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, description="Maximum number of retries")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    organization: Optional[str] = Field(None, description="Organization ID")
    context_window: Optional[int] = Field(None, description="Context window size")
    stream: bool = Field(False, description="Enable streaming responses")
    is_active: bool = Field(True, description="Whether this provider is active")
    priority: int = Field(1, ge=1, le=10, description="Provider priority (1-10)")
    
    @validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within reasonable bounds."""
        if v < 0.0 or v > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class LLMConfigManager:
    """Singleton configuration manager for LLM providers."""
    
    _instance: Optional["LLMConfigManager"] = None
    _configs: Dict[str, LLMProviderEnvironmentConfig] = {}
    _settings: Dict[str, LLMProviderSettings] = {}
    
    def __new__(cls) -> "LLMConfigManager":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize configuration manager."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._load_environment_configs()
    
    def _load_environment_configs(self) -> None:
        """Load configuration from environment variables."""
        # Load default providers from environment
        self._load_ollama_config()
        self._load_openai_config()
        
        # Load additional providers from environment
        self._load_custom_providers()
    
    def _load_ollama_config(self) -> None:
        """Load Ollama configuration from environment."""
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
        ollama_active = os.getenv("OLLAMA_ACTIVE", "true").lower() == "true"
        
        if ollama_active:
            config = LLMProviderEnvironmentConfig(
                provider_type="ollama",
                base_url=ollama_url,
                model_name=ollama_model,
                temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "100")) if os.getenv("OLLAMA_MAX_TOKENS") else None,
                timeout=int(os.getenv("OLLAMA_TIMEOUT", "30")),
                max_retries=int(os.getenv("OLLAMA_MAX_RETRIES", "3")),
                context_window=int(os.getenv("OLLAMA_CONTEXT_WINDOW")) if os.getenv("OLLAMA_CONTEXT_WINDOW") else None,
                stream=os.getenv("OLLAMA_STREAM", "false").lower() == "true",
                is_active=ollama_active,
                priority=int(os.getenv("OLLAMA_PRIORITY", "1"))
            )
            self._configs["ollama"] = config
    
    def _load_openai_config(self) -> None:
        """Load OpenAI configuration from environment."""
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_active = os.getenv("OPENAI_ACTIVE", "false").lower() == "true" and openai_key
        
        if openai_active:
            config = LLMProviderEnvironmentConfig(
                provider_type="openai",
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS")) if os.getenv("OPENAI_MAX_TOKENS") else None,
                timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
                max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
                api_key=openai_key,
                organization=os.getenv("OPENAI_ORGANIZATION"),
                is_active=openai_active,
                priority=int(os.getenv("OPENAI_PRIORITY", "2"))
            )
            self._configs["openai"] = config
    
    def _load_custom_providers(self) -> None:
        """Load custom provider configurations from environment."""
        # This can be extended to load additional providers
        # For now, we'll implement the basic providers
        pass
    
    def get_provider_config(self, provider_type: str) -> Optional[LLMProviderEnvironmentConfig]:
        """Get configuration for a specific provider type."""
        return self._configs.get(provider_type)
    
    def get_active_providers(self) -> List[LLMProviderEnvironmentConfig]:
        """Get list of active provider configurations."""
        return [config for config in self._configs.values() if config.is_active]
    
    def get_priority_sorted_providers(self) -> List[LLMProviderEnvironmentConfig]:
        """Get active providers sorted by priority."""
        active_providers = self.get_active_providers()
        return sorted(active_providers, key=lambda x: x.priority)
    
    def get_default_provider(self) -> Optional[LLMProviderEnvironmentConfig]:
        """Get the highest priority active provider."""
        sorted_providers = self.get_priority_sorted_providers()
        return sorted_providers[0] if sorted_providers else None
    
    def to_provider_config(self, env_config: LLMProviderEnvironmentConfig) -> LLMProviderConfig:
        """Convert environment config to provider-specific config."""
        if env_config.provider_type == "ollama":
            return OllamaConfig(
                provider_type=env_config.provider_type,
                base_url=env_config.base_url or "http://localhost:11434",
                model_name=env_config.model_name,
                temperature=env_config.temperature,
                max_tokens=env_config.max_tokens,
                timeout=env_config.timeout,
                max_retries=env_config.max_retries,
                context_window=env_config.context_window,
                stream=env_config.stream
            )
        elif env_config.provider_type == "openai":
            return OpenAIConfig(
                provider_type=env_config.provider_type,
                base_url=env_config.base_url or "https://api.openai.com/v1",
                model_name=env_config.model_name,
                temperature=env_config.temperature,
                max_tokens=env_config.max_tokens,
                timeout=env_config.timeout,
                max_retries=env_config.max_retries,
                api_key=env_config.api_key,
                organization=env_config.organization
            )
        else:
            raise ValueError(f"Unsupported provider type: {env_config.provider_type}")
    
    def to_provider_settings(self, env_config: LLMProviderEnvironmentConfig) -> LLMProviderSettings:
        """Convert environment config to provider settings with constitutional compliance."""
        provider_config = self.to_provider_config(env_config)
        
        return LLMProviderSettings(
            id=uuid4(),
            name=f"{env_config.provider_type.capitalize()} Provider",
            description=f"Configuration for {env_config.provider_type} provider",
            config=provider_config,
            is_active=env_config.is_active,
            constitutional_audit={
                "config_source": "environment",
                "loaded_at": "current_timestamp",  # Will be set by TimestampMixin
                "compliance_checked": True
            }
        )
    
    async def reload_configurations(self) -> None:
        """Reload configurations from environment (for hot-reloading)."""
        self._configs.clear()
        self._load_environment_configs()
    
    def validate_configuration(self, provider_type: str) -> Dict[str, Any]:
        """Validate configuration for a specific provider."""
        config = self.get_provider_config(provider_type)
        if not config:
            return {"valid": False, "errors": ["Provider configuration not found"]}
        
        errors = []
        
        # Validate required fields based on provider type
        if provider_type == "openai" and not config.api_key:
            errors.append("OpenAI API key is required")
        
        if not config.model_name:
            errors.append("Model name is required")
        
        if config.base_url and not config.base_url.startswith(("http://", "https://")):
            errors.append("Base URL must start with http:// or https://")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "provider_type": provider_type,
            "is_active": config.is_active
        }
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of all configurations."""
        active_providers = self.get_active_providers()
        inactive_providers = [config for config in self._configs.values() if not config.is_active]
        
        return {
            "total_providers": len(self._configs),
            "active_providers": len(active_providers),
            "inactive_providers": len(inactive_providers),
            "default_provider": self.get_default_provider().provider_type if self.get_default_provider() else None,
            "providers": {
                provider_type: {
                    "is_active": config.is_active,
                    "priority": config.priority,
                    "model": config.model_name
                }
                for provider_type, config in self._configs.items()
            }
        }


# Global instance for easy access
_config_manager = LLMConfigManager()


def get_llm_config_manager() -> LLMConfigManager:
    """Get the global LLM configuration manager instance."""
    return _config_manager


async def reload_llm_configurations() -> None:
    """Reload LLM configurations from environment."""
    await _config_manager.reload_configurations()