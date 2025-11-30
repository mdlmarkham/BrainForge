"""Abstract base class for LLM providers in BrainForge."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator

from src.config.llm import LLMProviderConfig


class LLMResponse(BaseModel):
    """Standard response model for LLM completions."""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used for generation")
    provider: str = Field(..., description="Provider name")
    usage: dict[str, int] | None = Field(None, description="Token usage information")
    finish_reason: str | None = Field(None, description="Reason for completion")
    constitutional_audit: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """Message model for chat completion."""

    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")

    @validator("role")
    def validate_role(cls, v: str) -> str:
        """Validate message role."""
        if v not in ("system", "user", "assistant"):
            raise ValueError("Role must be 'system', 'user', or 'assistant'")
        return v


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion."""

    messages: list[ChatMessage] = Field(..., description="List of chat messages")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(None, ge=1, description="Maximum tokens to generate")
    stream: bool = Field(False, description="Enable streaming responses")


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMProviderConfig):
        """Initialize provider with configuration."""
        self.config = config
        self._client = None

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate text completion from a prompt.

        Args:
            prompt: Input prompt for text generation
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    @abstractmethod
    async def chat_completion(self, request: ChatCompletionRequest) -> LLMResponse:
        """Generate chat completion from a conversation.

        Args:
            request: Chat completion request with messages

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and accessible.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def get_available_models(self) -> list[str]:
        """Get list of available models from the provider.

        Returns:
            List of available model names
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close provider connections and cleanup resources."""
        pass

    def _build_constitutional_audit(self, operation: str, **kwargs: Any) -> dict[str, Any]:
        """Build constitutional audit trail for LLM operations.

        Args:
            operation: Name of the operation being performed
            **kwargs: Additional audit information

        Returns:
            Constitutional audit dictionary
        """
        return {
            "operation": operation,
            "provider": self.config.provider_type,
            "model": self.config.model_name,
            "timestamp": datetime.utcnow().isoformat(),
            "compliance_checked": True,
            **kwargs
        }


class LLMError(Exception):
    """Base exception for all LLM-related errors."""

    def __init__(self, message: str, provider_type: str = "unknown", operation: str = "unknown"):
        super().__init__(message)
        self.provider_type = provider_type
        self.operation = operation
        self.constitutional_audit = {
            "error_type": self.__class__.__name__,
            "message": message,
            "provider": provider_type,
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat()
        }


class LLMProviderError(LLMError):
    """Base exception for LLM provider errors."""
    pass


class LLMTimeoutError(LLMError):
    """Exception for timeout errors in LLM operations."""
    pass


class ConnectionError(LLMProviderError):
    """Exception for connection-related errors."""
    pass


class AuthenticationError(LLMProviderError):
    """Exception for authentication errors."""
    pass


class RateLimitError(LLMProviderError):
    """Exception for rate limiting errors."""
    pass


class ModelNotFoundError(LLMProviderError):
    """Exception for model not found errors."""
    pass
