"""Ollama provider implementation for BrainForge LLM abstraction layer."""

import asyncio
from typing import Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from src.config.llm import OllamaConfig
from src.services.llm.base import (
    ChatCompletionRequest,
    ConnectionError,
    LLMProvider,
    LLMProviderError,
    LLMResponse,
    ModelNotFoundError,
    RateLimitError,
)


class OllamaProvider(LLMProvider):
    """Ollama provider implementation for local LLM inference."""

    def __init__(self, config: OllamaConfig):
        """Initialize Ollama provider with configuration."""
        super().__init__(config)
        self._session: ClientSession | None = None
        self._timeout = ClientTimeout(total=config.timeout)

    async def _ensure_session(self) -> ClientSession:
        """Ensure HTTP session is available."""
        if self._session is None or self._session.closed:
            self._session = ClientSession(timeout=self._timeout)
        return self._session

    async def _make_request(
        self,
        endpoint: str,
        data: dict[str, Any],
        retry_count: int = 0
    ) -> dict[str, Any]:
        """Make HTTP request to Ollama API with retry logic."""
        session = await self._ensure_session()
        url = f"{self.config.base_url}{endpoint}"

        try:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ModelNotFoundError(
                        f"Model {self.config.model_name} not found",
                        self.config.provider_type,
                        endpoint
                    )
                elif response.status == 429:
                    if retry_count < self.config.max_retries:
                        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                        return await self._make_request(endpoint, data, retry_count + 1)
                    raise RateLimitError(
                        "Rate limit exceeded",
                        self.config.provider_type,
                        endpoint
                    )
                else:
                    raise LLMProviderError(
                        f"HTTP {response.status}: {await response.text()}",
                        self.config.provider_type,
                        endpoint
                    )
        except aiohttp.ClientError as e:
            if retry_count < self.config.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(endpoint, data, retry_count + 1)
            raise ConnectionError(
              f"Connection error: {str(e)}",
              self.config.provider_type,
              endpoint
          ) from e

    async def generate_text(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate text completion using Ollama's generate endpoint."""
        data = {
            "model": self.config.model_name,
            "prompt": prompt,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            }
        }

        # Remove None values
        data["options"] = {k: v for k, v in data["options"].items() if v is not None}

        try:
            response_data = await self._make_request("/api/generate", data)

            # Ollama returns streaming responses, so we need to collect all chunks
            if self.config.stream:
                # For streaming, we'd need to handle the stream properly
                # For now, we'll implement non-streaming behavior
                # Skip streaming check and proceed with non-streaming
                content = response_data.get("response", "")
                usage = {
                    "prompt_tokens": response_data.get("prompt_eval_count", 0),
                    "completion_tokens": response_data.get("eval_count", 0),
                    "total_tokens": response_data.get("prompt_eval_count", 0) +
                                   response_data.get("eval_count", 0)
                }
                finish_reason = response_data.get("done_reason", "stop")
            else:
                content = response_data.get("response", "")
                usage = {
                    "prompt_tokens": response_data.get("prompt_eval_count", 0),
                    "completion_tokens": response_data.get("eval_count", 0),
                    "total_tokens": response_data.get("prompt_eval_count", 0) +
                                   response_data.get("eval_count", 0)
                }
                finish_reason = response_data.get("done_reason", "stop")

            return LLMResponse(
                content=content,
                model=self.config.model_name,
                provider=self.config.provider_type,
                usage=usage,
                finish_reason=finish_reason,
                constitutional_audit=self._build_constitutional_audit(
                    "generate_text",
                    prompt_length=len(prompt),
                    response_length=len(content)
                )
            )
        except Exception as e:
            if not isinstance(e, LLMProviderError):
                raise LLMProviderError(
                    f"Text generation failed: {str(e)}",
                    self.config.provider_type,
                    "generate_text"
                ) from e
            raise

    async def chat_completion(self, request: ChatCompletionRequest) -> LLMResponse:
        """Generate chat completion using Ollama's chat endpoint."""
        # Convert messages to Ollama format
        messages = []
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        data = {
            "model": self.config.model_name,
            "messages": messages,
            "options": {
                "temperature": request.temperature or self.config.temperature,
                "num_predict": request.max_tokens or self.config.max_tokens,
            },
            "stream": request.stream
        }

        # Remove None values
        data["options"] = {k: v for k, v in data["options"].items() if v is not None}

        try:
            response_data = await self._make_request("/api/chat", data)

            if request.stream:
                # Handle streaming response
                # Skip streaming check and proceed with non-streaming
                pass
            else:
                message = response_data.get("message", {})
                content = message.get("content", "")
                usage = {
                    "prompt_tokens": response_data.get("prompt_eval_count", 0),
                    "completion_tokens": response_data.get("eval_count", 0),
                    "total_tokens": response_data.get("prompt_eval_count", 0) +
                                   response_data.get("eval_count", 0)
                }
                finish_reason = response_data.get("done_reason", "stop")

            return LLMResponse(
                content=content,
                model=self.config.model_name,
                provider=self.config.provider_type,
                usage=usage,
                finish_reason=finish_reason,
                constitutional_audit=self._build_constitutional_audit(
                    "chat_completion",
                    message_count=len(messages),
                    response_length=len(content)
                )
            )
        except Exception as e:
            if not isinstance(e, LLMProviderError):
                raise LLMProviderError(
                    f"Chat completion failed: {str(e)}",
                    self.config.provider_type,
                    "chat_completion"
                ) from e
            raise

    async def health_check(self) -> bool:
        """Check if Ollama server is healthy and accessible."""
        try:
            session = await self._ensure_session()
            url = f"{self.config.base_url}/api/tags"

            async with session.get(url) as response:
                return response.status == 200
        except Exception:
            return False

    async def get_available_models(self) -> list[str]:
        """Get list of available models from Ollama server."""
        try:
            session = await self._ensure_session()
            url = f"{self.config.base_url}/api/tags"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    return [model.get("name", "") for model in models if model.get("name")]
                return []
        except Exception:
            return []

    async def close(self) -> None:
        """Close HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
