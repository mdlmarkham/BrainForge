"""Vector storage and retrieval service for semantic search.

This service handles vector operations including storage, retrieval,
and similarity search using PostgreSQL with PGVector extension.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from src.models.embedding import Embedding
from src.services.database import DatabaseService

logger = logging.getLogger(__name__)


class VectorStore:
    """Service for vector storage and similarity search operations."""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        self.default_distance_metric = "cosine"  # cosine distance for normalized vectors
        self.default_search_limit = 10

    async def store_vector(self, note_id: str, vector: list[float],
                          model_name: str, model_version: str) -> Embedding | None:
        """Store a vector in the database.
        
        Args:
            note_id: ID of the note this vector belongs to
            vector: The embedding vector to store
            model_name: Name of the embedding model
            model_version: Version of the embedding model
            
        Returns:
            Stored embedding record or None if storage fails
        """
        try:
            # Validate vector dimensions and values
            if not self._validate_vector(vector):
                logger.error("Invalid vector provided for storage")
                return None

            # Check if embedding already exists for this note
            existing_embedding = await self.database_service.get_embedding_by_note_id(note_id)
            if existing_embedding:
                logger.info(f"Updating existing embedding for note {note_id}")
                return await self.update_vector(note_id, vector, model_name, model_version)

            # Create new embedding record
            embedding_data = {
                "note_id": note_id,
                "vector": vector,
                "model_name": model_name,
                "model_version": model_version,
                "dimensions": len(vector),
                "normalized": True  # Assuming OpenAI embeddings are normalized
            }

            embedding = await self.database_service.create_embedding(embedding_data)
            logger.info(f"Stored vector for note {note_id}")
            return embedding

        except Exception as e:
            logger.error(f"Failed to store vector for note {note_id}: {e}")
            return None

    async def update_vector(self, note_id: str, new_vector: list[float],
                           model_name: str, model_version: str) -> Embedding | None:
        """Update an existing vector in the database.
        
        Args:
            note_id: ID of the note whose vector to update
            new_vector: New embedding vector
            model_name: Name of the embedding model
            model_version: Version of the embedding model
            
        Returns:
            Updated embedding record or None if update fails
        """
        try:
            if not self._validate_vector(new_vector):
                logger.error("Invalid vector provided for update")
                return None

            existing_embedding = await self.database_service.get_embedding_by_note_id(note_id)
            if not existing_embedding:
                logger.warning(f"No existing embedding found for note {note_id}")
                return None

            update_data = {
                "vector": new_vector,
                "model_name": model_name,
                "model_version": model_version,
                "dimensions": len(new_vector)
            }

            updated_embedding = await self.database_service.update_embedding(
                existing_embedding.id, update_data
            )
            logger.info(f"Updated vector for note {note_id}")
            return updated_embedding

        except Exception as e:
            logger.error(f"Failed to update vector for note {note_id}: {e}")
            return None

    async def get_vector(self, note_id: str) -> list[float] | None:
        """Retrieve a vector from the database.
        
        Args:
            note_id: ID of the note to retrieve vector for
            
        Returns:
            Embedding vector or None if not found
        """
        try:
            embedding = await self.database_service.get_embedding_by_note_id(note_id)
            if embedding and embedding.vector:
                return embedding.vector
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve vector for note {note_id}: {e}")
            return None

    async def similarity_search(self, query_vector: list[float],
                               limit: int = 10,
                               distance_metric: str = "cosine") -> list[tuple[Embedding, float]]:
        """Perform similarity search using vector distance.
        
        Args:
            query_vector: Query vector to compare against
            limit: Maximum number of results to return
            distance_metric: Distance metric to use ("cosine", "l2", "inner_product")
            
        Returns:
            List of (embedding, distance) tuples sorted by similarity
        """
        if not self._validate_vector(query_vector):
            logger.error("Invalid query vector provided for search")
            return []

        try:
            results = await self.database_service.similarity_search(
                query_vector=query_vector,
                limit=limit,
                distance_metric=distance_metric
            )

            logger.info(f"Similarity search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    async def hybrid_search(self, query_vector: list[float],
                           filters: dict[str, Any] = None,
                           limit: int = 10,
                           distance_metric: str = "cosine") -> list[tuple[Embedding, float]]:
        """Perform hybrid search combining vector similarity with metadata filtering.
        
        Args:
            query_vector: Query vector for semantic similarity
            filters: Metadata filters to apply
            limit: Maximum number of results
            distance_metric: Distance metric for vector comparison
            
        Returns:
            List of (embedding, distance) tuples
        """
        if not self._validate_vector(query_vector):
            logger.error("Invalid query vector provided for hybrid search")
            return []

        try:
            results = await self.database_service.hybrid_search(
                query_vector=query_vector,
                filters=filters or {},
                limit=limit,
                distance_metric=distance_metric
            )

            logger.info(f"Hybrid search returned {len(results)} results with filters: {filters}")
            return results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def batch_similarity_search(self, query_vectors: list[list[float]],
                                     limit_per_query: int = 5,
                                     distance_metric: str = "cosine") -> list[list[tuple[Embedding, float]]]:
        """Perform similarity search for multiple query vectors.
        
        Args:
            query_vectors: List of query vectors
            limit_per_query: Results limit per query
            distance_metric: Distance metric to use
            
        Returns:
            List of results for each query vector
        """
        valid_vectors = [vec for vec in query_vectors if self._validate_vector(vec)]
        if not valid_vectors:
            logger.warning("No valid query vectors provided for batch search")
            return []

        try:
            # Process queries in parallel
            tasks = []
            for query_vector in valid_vectors:
                task = self.similarity_search(
                    query_vector=query_vector,
                    limit=limit_per_query,
                    distance_metric=distance_metric
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Batch search task failed: {result}")
                    valid_results.append([])
                else:
                    valid_results.append(result)

            logger.info(f"Batch similarity search processed {len(valid_vectors)} queries")
            return valid_results

        except Exception as e:
            logger.error(f"Batch similarity search failed: {e}")
            return [[] for _ in valid_vectors]

    async def get_similar_notes(self, note_id: str, limit: int = 10) -> list[tuple[str, float]]:
        """Find notes similar to a given note.
        
        Args:
            note_id: ID of the reference note
            limit: Maximum number of similar notes to return
            
        Returns:
            List of (note_id, similarity_score) tuples
        """
        try:
            # Get the vector for the reference note
            reference_vector = await self.get_vector(note_id)
            if not reference_vector:
                logger.warning(f"No vector found for note {note_id}")
                return []

            # Perform similarity search
            similar_embeddings = await self.similarity_search(
                query_vector=reference_vector,
                limit=limit + 1,  # +1 to exclude the reference note itself
                distance_metric="cosine"
            )

            # Filter out the reference note and return note IDs with scores
            results = []
            for embedding, distance in similar_embeddings:
                if embedding.note_id != note_id:
                    # Convert distance to similarity score (1 - distance for cosine)
                    similarity_score = 1.0 - distance
                    results.append((embedding.note_id, similarity_score))

            # Limit results
            results = results[:limit]
            logger.info(f"Found {len(results)} similar notes for note {note_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to find similar notes for {note_id}: {e}")
            return []

    def _validate_vector(self, vector: list[float]) -> bool:
        """Validate that a vector meets requirements.
        
        Args:
            vector: The vector to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not vector:
            return False

        # Check dimensions (OpenAI text-embedding-3-small uses 1536 dimensions)
        if len(vector) != 1536:
            logger.warning(f"Invalid vector dimensions: {len(vector)} != 1536")
            return False

        # Check for valid numeric values
        for value in vector:
            if not isinstance(value, (int, float)):
                return False
            if not (-10 <= value <= 10):  # Reasonable range for embeddings
                logger.warning(f"Vector value out of expected range: {value}")
                return False

        return True

    async def get_vector_statistics(self) -> dict[str, Any]:
        """Get statistics about stored vectors.
        
        Returns:
            Dictionary with vector statistics
        """
        try:
            stats = await self.database_service.get_embedding_statistics()
            return {
                "total_vectors": stats.get("count", 0),
                "average_dimensions": stats.get("avg_dimensions", 0),
                "model_distribution": stats.get("models", {}),
                "storage_size_mb": stats.get("storage_size", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get vector statistics: {e}")
            return {}

    async def optimize_index(self) -> bool:
        """Optimize the vector index for better performance.
        
        Returns:
            True if optimization successful, False otherwise
        """
        try:
            success = await self.database_service.optimize_vector_index()
            if success:
                logger.info("Vector index optimization completed")
            else:
                logger.warning("Vector index optimization may not have completed fully")
            return success
        except Exception as e:
            logger.error(f"Vector index optimization failed: {e}")
            return False

    async def cleanup_orphaned_vectors(self) -> int:
        """Remove vectors that no longer have associated notes.
        
        Returns:
            Number of vectors removed
        """
        try:
            count = await self.database_service.cleanup_orphaned_embeddings()
            logger.info(f"Removed {count} orphaned vectors")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned vectors: {e}")
            return 0


class MockVectorStore(VectorStore):
    """Mock vector store for testing without database dependency."""

    def __init__(self, database_service: DatabaseService):
        super().__init__(database_service)
        self._vectors = {}  # In-memory storage for testing

    async def store_vector(self, note_id: str, vector: list[float],
                          model_name: str, model_version: str) -> Embedding | None:
        """Store vector in mock storage."""
        if not self._validate_vector(vector):
            return None

        # Create mock embedding
        embedding = Embedding(
            id=str(uuid.uuid4()),
            note_id=note_id,
            vector=vector,
            model_name=model_name,
            model_version=model_version,
            dimensions=len(vector),
            normalized=True,
            created_at=datetime.now()
        )

        self._vectors[note_id] = embedding
        return embedding

    async def get_vector(self, note_id: str) -> list[float] | None:
        """Retrieve vector from mock storage."""
        embedding = self._vectors.get(note_id)
        return embedding.vector if embedding else None

    async def similarity_search(self, query_vector: list[float],
                               limit: int = 10,
                               distance_metric: str = "cosine") -> list[tuple[Embedding, float]]:
        """Mock similarity search using cosine distance."""
        if not self._validate_vector(query_vector):
            return []

        results = []
        for embedding in self._vectors.values():
            # Simple mock cosine distance calculation
            distance = self._mock_cosine_distance(query_vector, embedding.vector)
            results.append((embedding, distance))

        # Sort by distance (ascending) and limit results
        results.sort(key=lambda x: x[1])
        return results[:limit]

    def _mock_cosine_distance(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate mock cosine distance between two vectors."""
        if len(vec1) != len(vec2):
            return 1.0  # Maximum distance for different dimensions

        # Simple mock implementation
        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 1.0

        cosine_similarity = dot_product / (norm1 * norm2)
        return 1.0 - cosine_similarity  # Convert to distance


# Factory function to create appropriate vector store
def create_vector_store(database_service: DatabaseService, use_mock: bool = False) -> VectorStore:
    """Create a vector store instance.
    
    Args:
        database_service: Database service instance
        use_mock: Whether to use mock store (for testing)
        
    Returns:
        Vector store instance
    """
    if use_mock:
        return MockVectorStore(database_service)
    else:
        return VectorStore(database_service)
