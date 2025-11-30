"""Unit tests for LLM provider abstraction layer."""

from unittest.mock import AsyncMock, patch

import pytest

from src.config.llm import OllamaConfig
from src.services.llm.base import (
    ChatCompletionRequest,
    ChatMessage,
    LLMProvider,
    LLMResponse,
    ModelNotFoundError,
    RateLimitError,
)
from src.services.llm.factory import LLMProviderFactory
from src.services.llm.ollama_provider import OllamaProvider


@pytest.mark.asyncio
class TestOllamaProvider:
    """Test suite for OllamaProvider."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = OllamaConfig(
            provider_type="ollama",
            base_url="http://localhost:11434",
            model_name="llama2",
            temperature=0.7,
            max_tokens=100,
            timeout=30,
            max_retries=3
        )
        self.provider = OllamaProvider(self.config)

    async def test_health_check_success(self):
        """Test successful health check."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await self.provider.health_check()

            assert result is True
            mock_get.assert_called_once_with(f"{self.config.base_url}/api/tags")

    async def test_health_check_failure(self):
        """Test health check failure."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await self.provider.health_check()

            assert result is False

    async def test_generate_text_success(self):
        """Test successful text generation."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "response": "Test response",
                "done": True
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await self.provider.generate_text("Test prompt")

            assert isinstance(result, LLMResponse)
            assert result.content == "Test response"
            assert result.provider == "ollama"
            assert result.model == "llama2"
            assert result.constitutional_audit["compliance_checked"] is True

    async def test_generate_text_streaming(self):
        """Test text generation with streaming."""
        self.config.stream = True

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200

            # Mock the JSON response directly instead of streaming
            mock_response.json.return_value = {
                "response": "Test response",
                "done": True,
                "prompt_eval_count": 10,
                "eval_count": 5,
                "done_reason": "stop"
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await self.provider.generate_text("Test prompt")

            assert isinstance(result, LLMResponse)
            assert result.content == "Test response"

    async def test_chat_completion_success(self):
        """Test successful chat completion."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "message": {"content": "Test chat response"},
                "done": True
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            messages = [
                ChatMessage(role="user", content="Hello")
            ]
            request = ChatCompletionRequest(messages=messages)

            result = await self.provider.chat_completion(request)

            assert isinstance(result, LLMResponse)
            assert result.content == "Test chat response"
            assert result.provider == "ollama"
            assert result.model == "llama2"

    async def test_list_models_success(self):
        """Test successful model listing."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama2", "size": 3826160512},
                    {"name": "mistral", "size": 4117920768}
                ]
            }
            mock_get.return_value.__aenter__.return_value = mock_response

            models = await self.provider.get_available_models()

            assert len(models) == 2
            assert models[0] == "llama2"
            assert models[1] == "mistral"


@pytest.mark.asyncio
class TestLLMProviderFactory:
    """Test suite for LLMProviderFactory."""

    async def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        config = OllamaConfig(
            provider_type="ollama",
            base_url="http://localhost:11434",
            model_name="llama2"
        )

        provider = LLMProviderFactory.create_provider(config)

        assert isinstance(provider, OllamaProvider)
        assert provider.config.provider_type == "ollama"
        assert provider.config.model_name == "llama2"

    async def test_create_from_settings(self):
        """Test creating provider from settings dictionary."""
        settings = {
            "provider_type": "ollama",
            "model_name": "llama2",
            "base_url": "http://localhost:11434"
        }

        provider = LLMProviderFactory.create_from_settings(settings)

        assert isinstance(provider, OllamaProvider)
        assert provider.config.provider_type == "ollama"
        assert provider.config.model_name == "llama2"

    async def test_get_available_providers(self):
        """Test getting available providers."""
        providers = LLMProviderFactory.get_available_providers()

        assert "ollama" in providers
        assert providers["ollama"] == OllamaProvider

    async def test_register_provider(self):
        """Test registering a new provider."""
        class TestProvider(LLMProvider):
            def __init__(self, config):
                super().__init__(config)

            async def generate_text(self, prompt: str) -> LLMResponse:
                return LLMResponse(content="test", provider="test", model="test")

            async def chat_completion(self, request: ChatCompletionRequest) -> LLMResponse:
                return LLMResponse(content="test", provider="test", model="test")

        LLMProviderFactory.register_provider("test", TestProvider)

        providers = LLMProviderFactory.get_available_providers()
        assert "test" in providers
        assert providers["test"] == TestProvider


@pytest.mark.asyncio
class TestLLMProviderErrorHandling:
    """Test suite for LLM provider error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = OllamaConfig(
            provider_type="ollama",
            base_url="http://localhost:11434",
            model_name="llama2"
        )
        self.provider = OllamaProvider(self.config)

    async def test_connection_error(self):
        """Test connection error handling."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                await self.provider.generate_text("Test prompt")

    async def test_rate_limit_error(self):
        """Test rate limit error handling."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(RateLimitError):
                await self.provider.generate_text("Test prompt")

    async def test_model_not_found_error(self):
        """Test model not found error handling."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.json.return_value = {"error": "Model not found"}
            mock_post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ModelNotFoundError):
                await self.provider.generate_text("Test prompt")


@pytest.mark.asyncio
class TestConstitutionalCompliance:
    """Test suite for constitutional compliance in LLM providers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = OllamaConfig(
            provider_type="ollama",
            base_url="http://localhost:11434",
            model_name="llama2"
        )
        self.provider = OllamaProvider(self.config)

    async def test_audit_trail_generation(self):
        """Test audit trail generation."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "response": "Test response",
                "done": True
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await self.provider.generate_text("Test prompt")

            assert "constitutional_audit" in result.model_dump()
            audit = result.constitutional_audit
            assert audit["compliance_checked"] is True
            assert audit["provider"] == "ollama"
            assert audit["model"] == "llama2"
            assert "timestamp" in audit
