"""Semantic search algorithm service with advanced ranking and scoring.

This service implements the core semantic search algorithm that combines
embedding generation, vector similarity search, and advanced result ranking.
"""

import asyncio
import logging
import math
import uuid
from datetime import datetime
from typing import Any

from src.models.embedding import Embedding
from src.models.note import Note
from src.services.database import DatabaseService
from src.services.embedding_generator import EmbeddingGenerator
from src.services.hnsw_index import HNSWIndex
from src.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class SemanticSearch:
    """Core semantic search service implementing advanced search algorithms."""

    def __init__(self,
                 embedding_generator: EmbeddingGenerator,
                 vector_store: VectorStore,
                 hnsw_index: HNSWIndex,
                 database_service: DatabaseService):
        self.embedding_generator = embedding_generator
        self.vector_store = vector_store
        self.hnsw_index = hnsw_index
        self.database_service = database_service

        # Default search configuration with advanced ranking parameters
        self.default_config = {
            "limit": 10,
            "distance_metric": "cosine",
            "ef_search": 40,
            "min_similarity": 0.3,  # Minimum similarity threshold
            "max_results": 100,     # Maximum results to consider before filtering

            # Advanced ranking parameters
            "semantic_weight": 0.7,     # Weight for semantic similarity
            "metadata_weight": 0.2,     # Weight for metadata relevance
            "quality_weight": 0.1,      # Weight for content quality
            "recency_decay_days": 30,   # Days for recency decay factor
            "content_length_boost": 0.1, # Boost for longer content
            "note_type_weights": {      # Weights for different note types
                "permanent": 1.2,
                "insight": 1.1,
                "literature": 1.0,
                "fleeting": 0.8,
                "agent_generated": 0.9
            }
        }

    async def semantic_search(self, query: str, config: dict[str, Any] = None) -> list[dict[str, Any]]:
        """Perform semantic search based on query meaning with advanced ranking."""

        if not query or not query.strip():
            logger.warning("Empty query provided for semantic search")
            return []

        try:
            search_config = {**self.default_config, **(config or {})}

            # Step 1: Generate embedding for query
            query_embedding = await self.embedding_generator.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Step 2: Perform vector similarity search
            vector_results = await self.vector_store.similarity_search(
                query_vector=query_embedding,
                limit=search_config["max_results"],
                distance_metric=search_config["distance_metric"]
            )

            # Step 3: Advanced filtering and ranking with multiple factors
            filtered_results = await self._advanced_filter_and_rank(
                vector_results,
                search_config
            )

            # Step 4: Enrich results with note metadata
            enriched_results = await self._enrich_results_with_metadata(filtered_results)

            logger.info(f"Advanced semantic search completed: {len(enriched_results)} results for query: '{query}'")
            return enriched_results

        except Exception as e:
            logger.error(f"Semantic search failed for query '{query}': {e}")
            return []

    async def _advanced_filter_and_rank(self, vector_results: list[tuple[Embedding, float]],
                                      config: dict[str, Any]) -> list[tuple[Embedding, float, dict[str, float]]]:
        """Advanced filtering and ranking with multiple scoring factors."""

        scored_results = []

        for embedding, distance in vector_results:
            base_similarity = 1.0 - distance  # Convert distance to similarity

            if base_similarity >= config["min_similarity"]:
                # Get note metadata for advanced scoring
                note = await self.database_service.get_note(embedding.note_id)
                if not note:
                    continue

                # Calculate advanced score with multiple factors
                advanced_score, score_breakdown = await self._calculate_advanced_score(
                    note, base_similarity, config
                )

                scored_results.append((embedding, advanced_score, score_breakdown))

        # Sort by advanced score (descending)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Apply limit
        return scored_results[:config["limit"]]

    async def _calculate_advanced_score(self, note: Note, base_similarity: float,
                                      config: dict[str, Any]) -> tuple[float, dict[str, float]]:
        """Calculate advanced score with multiple ranking factors."""

        score_breakdown = {"base_similarity": base_similarity}

        # Factor 1: Note type weighting
        note_type_weight = config["note_type_weights"].get(note.note_type.value, 1.0)
        note_type_score = base_similarity * note_type_weight
        score_breakdown["note_type_score"] = note_type_score

        # Factor 2: Content length normalization
        content_length = len(note.content)
        content_length_score = self._calculate_content_length_score(content_length, config)
        score_breakdown["content_length_score"] = content_length_score

        # Factor 3: Recency factor
        recency_score = self._calculate_recency_score(note.created_at, config)
        score_breakdown["recency_score"] = recency_score

        # Factor 4: Quality indicators
        quality_score = self._calculate_quality_score(note, config)
        score_breakdown["quality_score"] = quality_score

        # Factor 5: Metadata relevance (placeholder - would need actual metadata analysis)
        metadata_score = 0.5  # Placeholder
        score_breakdown["metadata_score"] = metadata_score

        # Combine all factors with configurable weights
        advanced_score = (
            config["semantic_weight"] * base_similarity +
            config["metadata_weight"] * metadata_score +
            config["quality_weight"] * quality_score +
            0.05 * content_length_score +  # Smaller weight for content length
            0.05 * recency_score           # Smaller weight for recency
        )

        # Apply note type weighting as multiplier
        advanced_score *= note_type_weight

        # Ensure score stays within valid range
        advanced_score = min(max(advanced_score, 0.0), 1.0)

        return advanced_score, score_breakdown

    def _calculate_content_length_score(self, content_length: int, config: dict[str, Any]) -> float:
        """Calculate score based on content length."""
        # Normalize content length (boost for longer, informative content)
        optimal_length = 500  # Optimal content length in characters
        length_ratio = min(content_length / optimal_length, 2.0)  # Cap at 2x optimal
        return math.log(1 + length_ratio) * config["content_length_boost"]

    def _calculate_recency_score(self, created_at: str, config: dict[str, Any]) -> float:
        """Calculate recency score with exponential decay."""
        try:
            # Parse creation date
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_ago = (datetime.now().astimezone() - created_date).days

            # Exponential decay: newer notes get higher scores
            decay_factor = math.exp(-days_ago / config["recency_decay_days"])
            return decay_factor

        except Exception:
            # If date parsing fails, return neutral score
            return 0.5

    def _calculate_quality_score(self, note: Note, config: dict[str, Any]) -> float:
        """Calculate quality score based on note characteristics."""
        quality_score = 0.5  # Base quality score

        # Quality indicator 1: AI-generated content (may have different quality)
        if note.is_ai_generated:
            quality_score += 0.1 if note.ai_justification else -0.1

        # Quality indicator 2: Version history (more versions might indicate refinement)
        # This would need access to version history - placeholder
        version_quality = 0.0  # Would be calculated based on version count and changes

        # Quality indicator 3: Completeness (placeholder for content analysis)
        completeness = 0.0  # Would analyze content structure, links, etc.

        return min(max(quality_score + version_quality + completeness, 0.0), 1.0)

    async def hybrid_search(self, query: str, filters: dict[str, Any] = None,
                           config: dict[str, Any] = None) -> list[dict[str, Any]]:
        """Perform hybrid search combining semantic and metadata filtering."""

        if not query or not query.strip():
            logger.warning("Empty query provided for hybrid search")
            return []

        try:
            search_config = {**self.default_config, **(config or {})}
            filters = filters or {}

            # Step 1: Generate embedding for query
            query_embedding = await self.embedding_generator.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Step 2: Perform hybrid search with metadata filtering
            hybrid_results = await self.vector_store.hybrid_search(
                query_vector=query_embedding,
                filters=filters,
                limit=search_config["max_results"],
                distance_metric=search_config["distance_metric"]
            )

            # Step 3: Calculate advanced hybrid scores
            scored_results = await self._calculate_advanced_hybrid_scores(hybrid_results, filters, search_config)

            # Step 4: Filter and limit results
            filtered_results = self._filter_hybrid_results(
                scored_results,
                search_config["min_similarity"],
                search_config["limit"]
            )

            # Step 5: Enrich results with metadata
            enriched_results = await self._enrich_results_with_metadata(filtered_results)

            logger.info(f"Hybrid search completed: {len(enriched_results)} results with filters: {filters}")
            return enriched_results

        except Exception as e:
            logger.error(f"Hybrid search failed for query '{query}': {e}")
            return []

    async def _calculate_advanced_hybrid_scores(self, hybrid_results: list[tuple[Embedding, float]],
                                              filters: dict[str, Any], config: dict[str, Any]) -> list[tuple[Embedding, float, float, float, dict[str, float]]]:
        """Calculate advanced hybrid scores with multiple factors."""

        scored_results = []

        for embedding, semantic_distance in hybrid_results:
            semantic_similarity = 1.0 - semantic_distance

            if semantic_similarity >= config["min_similarity"]:
                # Get note for advanced scoring
                note = await self.database_service.get_note(embedding.note_id)
                if not note:
                    continue

                # Calculate metadata relevance
                metadata_score = await self._calculate_metadata_relevance(note, filters)

                # Calculate advanced factors
                content_length_score = self._calculate_content_length_score(len(note.content), config)
                recency_score = self._calculate_recency_score(note.created_at, config)
                quality_score = self._calculate_quality_score(note, config)
                note_type_weight = config["note_type_weights"].get(note.note_type.value, 1.0)

                # Combine scores with advanced weighting
                hybrid_score = (
                    config["semantic_weight"] * semantic_similarity +
                    config["metadata_weight"] * metadata_score +
                    config["quality_weight"] * quality_score +
                    0.03 * content_length_score +
                    0.02 * recency_score
                ) * note_type_weight

                score_breakdown = {
                    "semantic_similarity": semantic_similarity,
                    "metadata_score": metadata_score,
                    "quality_score": quality_score,
                    "content_length_score": content_length_score,
                    "recency_score": recency_score,
                    "note_type_weight": note_type_weight
                }

                scored_results.append((embedding, semantic_similarity, metadata_score, hybrid_score, score_breakdown))

        return scored_results

    async def _calculate_metadata_relevance(self, note: Note, filters: dict[str, Any]) -> float:
        """Calculate metadata relevance score based on filter matching."""
        if not filters:
            return 0.5  # Neutral score when no filters

        relevance_score = 0.0
        matched_filters = 0

        for key, value in filters.items():
            if hasattr(note, key):
                note_value = getattr(note, key)
                if note_value == value:
                    relevance_score += 1.0
                    matched_filters += 1
            elif key in note.metadata:
                if note.metadata[key] == value:
                    relevance_score += 1.0
                    matched_filters += 1

        if matched_filters > 0:
            return relevance_score / len(filters)
        else:
            return 0.0  # No filter matches

    def _filter_hybrid_results(self, scored_results: list[tuple[Embedding, float, float, float, dict[str, float]]],
                              min_similarity: float, limit: int) -> list[tuple[Embedding, float, float, float, dict[str, float]]]:
        """Filter hybrid search results based on similarity thresholds."""
        filtered_results = [
            result for result in scored_results
            if result[1] >= min_similarity  # Semantic similarity threshold
        ]

        # Sort by hybrid score (descending)
        filtered_results.sort(key=lambda x: x[3], reverse=True)

        # Apply limit
        return filtered_results[:limit]

    async def _enrich_results_with_metadata(self, results: list) -> list[dict[str, Any]]:
        """Enrich search results with note metadata and scoring details."""
        enriched_results = []

        for i, result in enumerate(results):
            if len(result) == 3:  # Advanced semantic search results
                embedding, advanced_score, score_breakdown = result
                note_id = embedding.note_id
                result_data = {
                    "similarity_score": score_breakdown.get("base_similarity", advanced_score),
                    "metadata_score": 0.0,  # Not applicable for pure semantic search
                    "hybrid_score": advanced_score,
                    "advanced_score": advanced_score,
                    "score_breakdown": score_breakdown,
                    "rank": i + 1
                }
            else:  # Hybrid search results
                embedding, semantic_score, metadata_score, hybrid_score, score_breakdown = result
                note_id = embedding.note_id
                result_data = {
                    "similarity_score": semantic_score,
                    "metadata_score": metadata_score,
                    "hybrid_score": hybrid_score,
                    "advanced_score": hybrid_score,
                    "score_breakdown": score_breakdown,
                    "rank": i + 1
                }

            # Get note metadata
            note = await self.database_service.get_note(note_id)
            if note:
                result_data["note"] = note.dict()
                enriched_results.append(result_data)

        return enriched_results

    # Rest of the methods remain similar but would need to be updated for consistency
    async def find_similar_notes(self, note_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Find notes similar to a given note."""
        try:
            # Get similar notes using vector similarity
            similar_notes = await self.vector_store.get_similar_notes(note_id, limit)

            # Enrich with note metadata
            enriched_results = []
            for similar_note_id, similarity_score in similar_notes:
                note = await self.database_service.get_note(similar_note_id)
                if note:
                    enriched_results.append({
                        "note": note.dict(),
                        "similarity_score": similarity_score,
                        "rank": len(enriched_results) + 1
                    })

            logger.info(f"Found {len(enriched_results)} similar notes for note {note_id}")
            return enriched_results

        except Exception as e:
            logger.error(f"Failed to find similar notes for {note_id}: {e}")
            return []

    async def batch_semantic_search(self, queries: list[str],
                                   config: dict[str, Any] = None) -> list[list[dict[str, Any]]]:
        """Perform semantic search for multiple queries in batch."""
        valid_queries = [q for q in queries if q and q.strip()]
        if not valid_queries:
            return []

        try:
            # Process queries in parallel
            tasks = []
            for query in valid_queries:
                task = self.semantic_search(query, config)
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

            logger.info(f"Batch semantic search processed {len(valid_queries)} queries")
            return valid_results

        except Exception as e:
            logger.error(f"Batch semantic search failed: {e}")
            return [[] for _ in valid_queries]


class MockSemanticSearch(SemanticSearch):
    """Mock semantic search service for testing."""

    def __init__(self,
                 embedding_generator: EmbeddingGenerator,
                 vector_store: VectorStore,
                 hnsw_index: HNSWIndex,
                 database_service: DatabaseService):
        super().__init__(embedding_generator, vector_store, hnsw_index, database_service)

    async def semantic_search(self, query: str, config: dict[str, Any] = None) -> list[dict[str, Any]]:
        """Mock semantic search implementation."""
        # Return mock results for testing
        return [
            {
                "note": {
                    "id": str(uuid.uuid4()),
                    "title": f"Mock result for: {query}",
                    "content": "This is a mock search result for testing purposes.",
                    "note_type": "literature",
                    "tags": ["test", "mock"],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "created_by": "test_user",
                    "is_ai_generated": False,
                    "ai_justification": None,
                    "version": 1
                },
                "similarity_score": 0.85,
                "metadata_score": 0.0,
                "hybrid_score": 0.85,
                "advanced_score": 0.85,
                "score_breakdown": {
                    "base_similarity": 0.85,
                    "note_type_score": 0.85,
                    "content_length_score": 0.05,
                    "recency_score": 0.5,
                    "quality_score": 0.5
                },
                "rank": 1
            }
        ]


# Factory function to create appropriate semantic search service
def create_semantic_search(embedding_generator: EmbeddingGenerator,
                          vector_store: VectorStore,
                          hnsw_index: HNSWIndex,
                          database_service: DatabaseService,
                          use_mock: bool = False) -> SemanticSearch:
    """Create a semantic search service instance."""
    if use_mock:
        return MockSemanticSearch(embedding_generator, vector_store, hnsw_index, database_service)
    else:
        return SemanticSearch(embedding_generator, vector_store, hnsw_index, database_service)


# Alias for backward compatibility
SemanticSearchService = SemanticSearch
