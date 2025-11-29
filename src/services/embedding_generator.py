"""Embedding generation service for semantic search with comprehensive error handling.

This service handles embedding generation using OpenAI's text-embedding-3-small model
with robust error handling, retry mechanisms, fallback strategies, and constitutional compliance.
"""

import asyncio
import logging
import os
import random
from datetime import datetime
from typing import Any

# Import OpenAI client (will be mocked for testing)
try:
    from openai import (
        APIConnectionError,
        APIError,
        APITimeoutError,
        OpenAI,
        RateLimitError,
    )
    from openai.types import CreateEmbeddingResponse
except ImportError:
    # Mock for development without OpenAI dependency
    OpenAI = None
    CreateEmbeddingResponse = None
    APIError = Exception
    RateLimitError = Exception
    APIConnectionError = Exception
    APITimeoutError = Exception

from src.models.embedding import Embedding, EmbeddingCreate
from src.services.database import DatabaseService

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Service for generating and managing text embeddings with robust error handling."""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        self.openai_client = None
        self.model_name = "text-embedding-3-small"
        self.model_version = "1.0"
        self.dimensions = 1536

        # Error handling and retry configuration
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,  # seconds
            "max_delay": 10.0,  # seconds
            "backoff_factor": 2.0,
            "jitter": True
        }

        # Fallback configuration
        self.fallback_config = {
            "use_fallback": True,
            "fallback_model": "sentence-transformers/all-MiniLM-L6-v2",  # Placeholder for local model
            "fallback_dimensions": 384
        }

        # Health monitoring
        self.health_status = {
            "last_success": None,
            "consecutive_failures": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "error_count": 0
        }

        self._initialize_openai_client()

    def _initialize_openai_client(self):
        """Initialize OpenAI client with configuration and error handling."""
        try:
            # Use environment variable for API key (security best practice)
            api_key = os.getenv('OPENAI_API_KEY')

            if not api_key:
                logger.warning("OPENAI_API_KEY environment variable not configured")
                self.openai_client = None
                self.health_status["error_count"] += 1
                return

            # Initialize OpenAI client with environment variable
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
            self.health_status["last_success"] = datetime.now()
        except Exception as e:
            logger.warning(f"OpenAI client initialization failed: {e}")
            self.openai_client = None
            self.health_status["error_count"] += 1

    async def generate_embedding(self, text: str, use_fallback: bool = True) -> list[float] | None:
        """Generate embedding for a single text with comprehensive error handling.
        
        Args:
            text: The text to generate embedding for
            use_fallback: Whether to use fallback strategy if primary method fails
            
        Returns:
            Embedding vector or None if all generation attempts fail
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None

        self.health_status["total_requests"] += 1

        # Try primary OpenAI API with retry mechanism
        embedding = await self._generate_with_retry(text)

        if embedding is not None:
            self.health_status["successful_requests"] += 1
            self.health_status["consecutive_failures"] = 0
            self.health_status["last_success"] = datetime.now()
            return embedding

        # If primary method fails and fallback is enabled
        if use_fallback and self.fallback_config["use_fallback"]:
            logger.warning(f"Primary embedding generation failed, attempting fallback for text: {text[:100]}...")
            return await self._generate_fallback_embedding(text)

        self.health_status["consecutive_failures"] += 1
        self.health_status["error_count"] += 1
        return None

    async def _generate_with_retry(self, text: str) -> list[float] | None:
        """Generate embedding with exponential backoff retry mechanism."""

        # Check if OpenAI client is available before attempting API calls
        if not self.openai_client:
            logger.warning("OpenAI client not available - API key may not be configured")
            return None

        for attempt in range(self.retry_config["max_retries"] + 1):
            try:

                # Generate embedding using OpenAI API
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.openai_client.embeddings.create(
                        model=self.model_name,
                        input=text,
                        dimensions=self.dimensions
                    )
                )

                if response and response.data:
                    embedding_vector = response.data[0].embedding
                    logger.debug(f"Generated embedding with {len(embedding_vector)} dimensions (attempt {attempt + 1})")
                    return embedding_vector
                else:
                    logger.error("Empty response from OpenAI embedding API")
                    return None

            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded (attempt {attempt + 1}): {e}")
                if attempt < self.retry_config["max_retries"]:
                    await self._wait_before_retry(attempt, "rate_limit")
                else:
                    logger.error("Max retries exceeded for rate limit")
                    return None

            except (APIConnectionError, APITimeoutError) as e:
                logger.warning(f"API connection error (attempt {attempt + 1}): {e}")
                if attempt < self.retry_config["max_retries"]:
                    await self._wait_before_retry(attempt, "connection")
                else:
                    logger.error("Max retries exceeded for connection issues")
                    return None

            except APIError as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt < self.retry_config["max_retries"]:
                    await self._wait_before_retry(attempt, "api_error")
                else:
                    logger.error("Max retries exceeded for API errors")
                    return None

            except Exception as e:
                logger.error(f"Unexpected error in embedding generation (attempt {attempt + 1}): {e}")
                if attempt < self.retry_config["max_retries"]:
                    await self._wait_before_retry(attempt, "unexpected")
                else:
                    logger.error("Max retries exceeded for unexpected errors")
                    return None

        return None

    async def _wait_before_retry(self, attempt: int, error_type: str):
        """Wait before retry with exponential backoff and jitter."""
        base_delay = self.retry_config["base_delay"]
        max_delay = self.retry_config["max_delay"]
        backoff_factor = self.retry_config["backoff_factor"]
        use_jitter = self.retry_config["jitter"]

        # Calculate delay with exponential backoff
        delay = min(base_delay * (backoff_factor ** attempt), max_delay)

        # Add jitter to avoid thundering herd problem
        if use_jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        logger.info(f"Waiting {delay:.2f}s before retry (attempt {attempt + 1}, error: {error_type})")
        await asyncio.sleep(delay)

    async def _generate_fallback_embedding(self, text: str) -> list[float] | None:
        """Generate embedding using fallback method (placeholder implementation)."""
        try:
            # This would implement a local embedding model or alternative service
            # For now, return a simple mock embedding
            logger.info(f"Using fallback embedding generation for text: {text[:100]}...")

            # Mock fallback embedding (simple hash-based approach for demonstration)
            import hashlib
            hash_object = hashlib.sha256(text.encode())
            hash_hex = hash_object.hexdigest()

            # Convert hash to numerical vector (simplified approach)
            embedding_vector = []
            for i in range(0, min(len(hash_hex), self.fallback_config["fallback_dimensions"]), 2):
                hex_pair = hash_hex[i:i+2]
                if len(hex_pair) == 2:
                    value = int(hex_pair, 16) / 255.0  # Normalize to [0, 1]
                    embedding_vector.append(value)

            # Pad or truncate to required dimensions
            while len(embedding_vector) < self.fallback_config["fallback_dimensions"]:
                embedding_vector.append(0.0)
            embedding_vector = embedding_vector[:self.fallback_config["fallback_dimensions"]]

            logger.info(f"Generated fallback embedding with {len(embedding_vector)} dimensions")
            return embedding_vector

        except Exception as e:
            logger.error(f"Fallback embedding generation failed: {e}")
            return None

    async def generate_embeddings_batch(self, texts: list[str], use_fallback: bool = True) -> list[list[float] | None]:
        """Generate embeddings for multiple texts in batch with error handling."""
        if not texts:
            return []

        self.health_status["total_requests"] += len(texts)

        # Process in batches to avoid API limits
        batch_size = 10  # Adjust based on API limits
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = await self._process_batch_with_fallback(batch, use_fallback)
            results.extend(batch_results)

        successful_count = sum(1 for result in results if result is not None)
        self.health_status["successful_requests"] += successful_count

        if successful_count < len(texts):
            failed_count = len(texts) - successful_count
            self.health_status["consecutive_failures"] += 1
            self.health_status["error_count"] += failed_count
            logger.warning(f"Batch processing: {successful_count} successful, {failed_count} failed")
        else:
            self.health_status["consecutive_failures"] = 0
            self.health_status["last_success"] = datetime.now()

        return results

    async def _process_batch_with_fallback(self, texts: list[str], use_fallback: bool) -> list[list[float] | None]:
        """Process a batch of texts with fallback mechanism."""
        try:
            # Try primary method first
            batch_results = await self._process_batch(texts)

            # Check for failures and apply fallback if needed
            if use_fallback and any(result is None for result in batch_results):
                fallback_results = []
                for i, (text, result) in enumerate(zip(texts, batch_results, strict=False)):
                    if result is None:
                        logger.warning(f"Primary batch embedding failed for text {i}, using fallback")
                        fallback_result = await self._generate_fallback_embedding(text)
                        fallback_results.append(fallback_result)
                    else:
                        fallback_results.append(result)
                return fallback_results

            return batch_results

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            if use_fallback:
                # Fallback to individual generation
                logger.warning("Batch processing failed, falling back to individual generation")
                individual_results = []
                for text in texts:
                    result = await self.generate_embedding(text, use_fallback=True)
                    individual_results.append(result)
                return individual_results
            else:
                return [None] * len(texts)

    async def _process_batch(self, texts: list[str]) -> list[list[float] | None]:
        """Process a batch of texts for embedding generation."""
        # Check if OpenAI client is available before attempting API calls
        if not self.openai_client:
            logger.warning("OpenAI client not available - API key may not be configured")
            return [None] * len(texts)

        try:

            # Filter out empty texts
            valid_texts = [text for text in texts if text and text.strip()]
            if not valid_texts:
                return [None] * len(texts)

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.embeddings.create(
                    model=self.model_name,
                    input=valid_texts,
                    dimensions=self.dimensions
                )
            )

            # Map results back to original text order
            results = []
            text_index = 0

            for text in texts:
                if text and text.strip() and text_index < len(response.data):
                    results.append(response.data[text_index].embedding)
                    text_index += 1
                else:
                    results.append(None)

            return results

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            return [None] * len(texts)

    async def health_check(self) -> dict[str, Any]:
        """Perform health check of the embedding service."""
        health_status = {
            "status": "healthy",
            "service": "embedding_generator",
            "timestamp": datetime.now().isoformat(),
            **self.health_status
        }

        # Check consecutive failures
        if self.health_status["consecutive_failures"] > 5:
            health_status["status"] = "degraded"
            health_status["reason"] = "high consecutive failure rate"

        # Check last success time
        if self.health_status["last_success"]:
            time_since_last_success = (datetime.now() - self.health_status["last_success"]).total_seconds()
            if time_since_last_success > 300:  # 5 minutes
                health_status["status"] = "degraded"
                health_status["reason"] = f"no successful requests for {time_since_last_success:.0f}s"

        # Check error rate
        total_requests = self.health_status["total_requests"]
        if total_requests > 0:
            error_rate = self.health_status["error_count"] / total_requests
            health_status["error_rate"] = error_rate
            if error_rate > 0.5:  # 50% error rate
                health_status["status"] = "unhealthy"
                health_status["reason"] = f"high error rate: {error_rate:.2%}"

        # Check OpenAI client status
        health_status["openai_client_available"] = self.openai_client is not None
        if not self.openai_client:
            health_status["status"] = "degraded"
            health_status["reason"] = "OpenAI client not available"

        return health_status

    async def reset_health_stats(self):
        """Reset health statistics (useful for testing or recovery)."""
        self.health_status = {
            "last_success": None,
            "consecutive_failures": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "error_count": 0
        }
        logger.info("Health statistics reset")

    # Database operations with error handling
    async def create_embedding_record(self, note_id: str, embedding_vector: list[float]) -> Embedding | None:
        """Create an embedding record in the database with error handling."""
        if not embedding_vector or len(embedding_vector) != self.dimensions:
            logger.error(f"Invalid embedding vector dimensions: {len(embedding_vector)}")
            return None

        try:
            embedding_data = EmbeddingCreate(
                note_id=note_id,
                vector=embedding_vector,
                model_version=self.model_version
            )

            embedding = await self.database_service.create_embedding(embedding_data)
            logger.info(f"Created embedding record for note {note_id}")
            return embedding

        except Exception as e:
            logger.error(f"Failed to create embedding record: {e}")
            return None

    async def get_embedding_for_note(self, note_id: str) -> Embedding | None:
        """Retrieve embedding for a specific note with error handling."""
        try:
            embedding = await self.database_service.get_embedding_by_note_id(note_id)
            return embedding
        except Exception as e:
            logger.error(f"Failed to retrieve embedding for note {note_id}: {e}")
            return None

    async def update_embedding(self, note_id: str, new_embedding_vector: list[float]) -> Embedding | None:
        """Update embedding for a note with error handling."""
        if not new_embedding_vector or len(new_embedding_vector) != self.dimensions:
            logger.error(f"Invalid embedding vector dimensions: {len(new_embedding_vector)}")
            return None

        try:
            # Get existing embedding
            existing_embedding = await self.get_embedding_for_note(note_id)
            if not existing_embedding:
                logger.warning(f"No existing embedding found for note {note_id}")
                return None

            # Update embedding
            updated_embedding = await self.database_service.update_embedding(
                existing_embedding.id,
                {"vector": new_embedding_vector, "model_version": self.model_version}
            )
            logger.info(f"Updated embedding for note {note_id}")
            return updated_embedding

        except Exception as e:
            logger.error(f"Failed to update embedding for note {note_id}: {e}")
            return None
