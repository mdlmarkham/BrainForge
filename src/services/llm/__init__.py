"""LLM Provider abstraction layer for BrainForge.

This module provides a provider-agnostic interface for LLM operations,
supporting multiple LLM providers through a unified API.
"""

from src.services.llm.base import (
    AuthenticationError,
    ChatCompletionRequest,
    ChatMessage,
    ConnectionError,
    LLMProvider,
    LLMProviderError,
    LLMResponse,
    ModelNotFoundError,
    RateLimitError,
)
from src.services.llm.factory import LLMProviderFactory, create_llm_provider
from src.services.llm.ollama_provider import OllamaProvider

__all__ = [
    # Base classes and models
    "LLMProvider",
    "LLMResponse",
    "ChatMessage",
    "ChatCompletionRequest",

    # Error classes
    "LLMProviderError",
    "ConnectionError",
    "AuthenticationError",
    "RateLimitError",
    "ModelNotFoundError",

    # Provider implementations
    "OllamaProvider",

    # Factory and utilities
    "LLMProviderFactory",
    "create_llm_provider",
]
