"""LLM provider configuration models for BrainForge."""

from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import Field, validator

from src.models.base import BrainForgeBaseModel, ProvenanceMixin, TimestampMixin


class LLMProviderConfig(BrainForgeBaseModel):
    """Base configuration model for LLM providers."""

    provider_type: str = Field(..., description="Type of LLM provider (e.g., 'ollama', 'openai')")
    base_url: str | None = Field(None, description="Base URL for the provider API")
    model_name: str = Field(..., description="Model name to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(None, ge=1, description="Maximum tokens to generate")
    timeout: int = Field(30, ge=1, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, description="Maximum number of retries")

    @validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within reasonable bounds."""
        if v < 0.0 or v > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class OllamaConfig(LLMProviderConfig):
    """Configuration model for Ollama provider."""

    provider_type: Literal["ollama"] = "ollama"
    base_url: str = Field("http://localhost:11434", description="Ollama server URL")
    context_window: int | None = Field(None, description="Context window size")
    stream: bool = Field(False, description="Enable streaming responses")

    @validator("base_url")
    def validate_base_url(cls, v: str) -> str:
        """Validate Ollama base URL."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip("/")


class OpenAIConfig(LLMProviderConfig):
    """Configuration model for OpenAI provider."""

    provider_type: Literal["openai"] = "openai"
    base_url: str = Field("https://api.openai.com/v1", description="OpenAI API URL")
    api_key: str | None = Field(None, description="OpenAI API key")
    organization: str | None = Field(None, description="OpenAI organization ID")


class LLMProviderSettings(BrainForgeBaseModel, TimestampMixin, ProvenanceMixin):
    """Complete LLM provider settings with constitutional compliance."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255, description="Provider settings name")
    description: str | None = Field(None, max_length=1000, description="Provider description")
    config: LLMProviderConfig = Field(..., description="Provider configuration")
    is_active: bool = Field(True, description="Whether this provider is active")
    constitutional_audit: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# Union type for all supported provider configs
ProviderConfig = OllamaConfig | OpenAIConfig
