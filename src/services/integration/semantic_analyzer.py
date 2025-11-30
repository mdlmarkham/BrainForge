"""Semantic analysis service for content integration using vector similarity."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.content_source import ContentSource
from ...services.semantic_search import SemanticSearchService
from ...services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """Analyzes semantic similarity between content sources for integration purposes."""

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.semantic_search = SemanticSearchService()

    async def analyze_similarity(self, db: AsyncSession, content_source: ContentSource,
                               similarity_threshold: float = 0.7) -> dict[str, Any]:
        """Analyze semantic similarity between the content source and existing knowledge."""

        try:
            # Generate embedding for the content source
            content_embedding = await self._generate_content_embedding(content_source)

            if not content_embedding:
                return self._get_default_similarity_analysis()

            # Search for similar content in the knowledge base
            similar_content = await self.semantic_search.find_similar_content(
                db, content_embedding, limit=10, similarity_threshold=similarity_threshold
            )

            # Analyze similarity patterns
            similarity_analysis = self._analyze_similarity_patterns(similar_content, similarity_threshold)

            # Add content-specific insights
            similarity_analysis.update({
                "content_source_id": str(content_source.id),
                "similarity_threshold_used": similarity_threshold,
                "total_similar_items_found": len(similar_content),
                "content_type": content_source.source_type
            })

            logger.info(f"Semantic analysis completed for content source {content_source.id}")
            return similarity_analysis

        except Exception as e:
            logger.error(f"Semantic analysis failed for content source {content_source.id}: {e}")
            return self._get_default_similarity_analysis()

    async def _generate_content_embedding(self, content_source: ContentSource) -> list[float] | None:
        """Generate embedding vector for content source."""

        try:
            # Combine content text for embedding
            content_text = self._prepare_content_for_embedding(content_source)

            if not content_text:
                return None

            # Generate embedding using the vector store service
            embedding = await self.vector_store.generate_embedding(content_text)
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding for content source {content_source.id}: {e}")
            return None

    def _prepare_content_for_embedding(self, content_source: ContentSource) -> str:
        """Prepare content text for embedding generation."""

        text_parts = []

        # Add title (most important for semantic matching)
        if content_source.title:
            text_parts.append(content_source.title)

        # Add description
        if content_source.description:
            text_parts.append(content_source.description)

        # Add content excerpt if available
        if hasattr(content_source, 'content') and content_source.content:
            content = content_source.content
            # Use first 500 characters for efficiency
            if len(content) > 500:
                content = content[:500] + "..."
            text_parts.append(content)

        return " ".join(text_parts)

    def _analyze_similarity_patterns(self, similar_content: list[dict],
                                   similarity_threshold: float) -> dict[str, Any]:
        """Analyze patterns in similarity results."""

        if not similar_content:
            return {
                "average_similarity": 0.0,
                "max_similarity": 0.0,
                "similarity_distribution": [],
                "strong_matches": 0,
                "weak_matches": 0,
                "similarity_insights": ["No similar content found in knowledge base"]
            }

        # Extract similarity scores
        similarity_scores = [item.get('similarity', 0.0) for item in similar_content]

        # Calculate statistics
        average_similarity = sum(similarity_scores) / len(similarity_scores)
        max_similarity = max(similarity_scores)

        # Count matches by strength
        strong_matches = len([score for score in similarity_scores if score >= similarity_threshold])
        weak_matches = len([score for score in similarity_scores if score < similarity_threshold])

        # Generate insights
        insights = self._generate_similarity_insights(similar_content, average_similarity, max_similarity)

        return {
            "average_similarity": round(average_similarity, 3),
            "max_similarity": round(max_similarity, 3),
            "similarity_distribution": self._get_similarity_distribution(similarity_scores),
            "strong_matches": strong_matches,
            "weak_matches": weak_matches,
            "similarity_insights": insights
        }

    def _generate_similarity_insights(self, similar_content: list[dict],
                                    average_similarity: float, max_similarity: float) -> list[str]:
        """Generate insights based on similarity analysis."""

        insights = []

        if max_similarity >= 0.9:
            insights.append("Very strong semantic match found - high integration potential")
        elif max_similarity >= 0.7:
            insights.append("Strong semantic match found - good integration potential")
        elif max_similarity >= 0.5:
            insights.append("Moderate semantic match - standard integration approach recommended")
        else:
            insights.append("Weak semantic match - consider basic integration or new category")

        if average_similarity >= 0.6:
            insights.append("Content shows consistent similarity with existing knowledge")
        else:
            insights.append("Content has limited similarity with existing knowledge")

        # Add insights based on match count
        match_count = len(similar_content)
        if match_count >= 5:
            insights.append(f"Found {match_count} similar items - rich context available")
        elif match_count >= 2:
            insights.append(f"Found {match_count} similar items - moderate context available")
        else:
            insights.append("Limited similar content found - may require new knowledge structures")

        return insights

    def _get_similarity_distribution(self, similarity_scores: list[float]) -> list[dict]:
        """Get distribution of similarity scores."""

        distribution = []
        ranges = [
            (0.9, 1.0, "Very High"),
            (0.7, 0.9, "High"),
            (0.5, 0.7, "Medium"),
            (0.3, 0.5, "Low"),
            (0.0, 0.3, "Very Low")
        ]

        for min_score, max_score, label in ranges:
            count = len([score for score in similarity_scores if min_score <= score < max_score])
            distribution.append({
                "range": label,
                "min_score": min_score,
                "max_score": max_score,
                "count": count
            })

        return distribution

    def _get_default_similarity_analysis(self) -> dict[str, Any]:
        """Get default similarity analysis when analysis fails."""

        return {
            "average_similarity": 0.0,
            "max_similarity": 0.0,
            "similarity_distribution": [],
            "strong_matches": 0,
            "weak_matches": 0,
            "similarity_insights": ["Semantic analysis unavailable - using default integration strategy"],
            "analysis_status": "failed"
        }

    async def compare_multiple_sources(self, db: AsyncSession, content_sources: list[ContentSource]) -> dict[str, Any]:
        """Compare semantic similarity between multiple content sources."""

        comparisons = []

        for i, source1 in enumerate(content_sources):
            for j, source2 in enumerate(content_sources):
                if i < j:  # Avoid duplicate comparisons
                    similarity = await self._compare_two_sources(db, source1, source2)
                    comparisons.append({
                        "source1_id": str(source1.id),
                        "source2_id": str(source2.id),
                        "similarity_score": similarity,
                        "source1_title": source1.title,
                        "source2_title": source2.title
                    })

        # Analyze comparison patterns
        comparison_analysis = self._analyze_comparison_patterns(comparisons)

        return {
            "pairwise_comparisons": comparisons,
            "comparison_analysis": comparison_analysis,
            "total_comparisons": len(comparisons)
        }

    async def _compare_two_sources(self, db: AsyncSession, source1: ContentSource,
                                 source2: ContentSource) -> float:
        """Compare semantic similarity between two content sources."""

        try:
            # Generate embeddings for both sources
            embedding1 = await self._generate_content_embedding(source1)
            embedding2 = await self._generate_content_embedding(source2)

            if not embedding1 or not embedding2:
                return 0.0

            # Calculate cosine similarity
            similarity = await self.vector_store.calculate_similarity(embedding1, embedding2)
            return similarity

        except Exception as e:
            logger.error(f"Failed to compare sources {source1.id} and {source2.id}: {e}")
            return 0.0

    def _analyze_comparison_patterns(self, comparisons: list[dict]) -> dict[str, Any]:
        """Analyze patterns in pairwise comparisons."""

        if not comparisons:
            return {"average_similarity": 0.0, "similarity_clusters": []}

        similarity_scores = [comp["similarity_score"] for comp in comparisons]
        average_similarity = sum(similarity_scores) / len(similarity_scores)

        # Identify similarity clusters
        clusters = self._identify_similarity_clusters(comparisons)

        return {
            "average_similarity": round(average_similarity, 3),
            "similarity_clusters": clusters,
            "high_similarity_pairs": len([score for score in similarity_scores if score >= 0.7]),
            "low_similarity_pairs": len([score for score in similarity_scores if score < 0.3])
        }

    def _identify_similarity_clusters(self, comparisons: list[dict]) -> list[dict]:
        """Identify clusters of highly similar content sources."""

        # Simple clustering based on similarity threshold
        clusters = []
        threshold = 0.7

        # Group sources by high similarity
        visited_sources = set()

        for comp in comparisons:
            if comp["similarity_score"] >= threshold:
                source1 = comp["source1_id"]
                source2 = comp["source2_id"]

                # Check if sources are already in clusters
                found_cluster = None
                for cluster in clusters:
                    if source1 in cluster["sources"] or source2 in cluster["sources"]:
                        found_cluster = cluster
                        break

                if found_cluster:
                    # Add both sources to existing cluster
                    if source1 not in found_cluster["sources"]:
                        found_cluster["sources"].append(source1)
                    if source2 not in found_cluster["sources"]:
                        found_cluster["sources"].append(source2)
                    found_cluster["average_similarity"] = (
                        found_cluster["average_similarity"] + comp["similarity_score"]
                    ) / 2
                else:
                    # Create new cluster
                    clusters.append({
                        "sources": [source1, source2],
                        "average_similarity": comp["similarity_score"],
                        "size": 2
                    })

                visited_sources.add(source1)
                visited_sources.add(source2)

        return clusters

    async def get_semantic_neighbors(self, db: AsyncSession, content_source: ContentSource,
                                   max_neighbors: int = 5) -> list[dict]:
        """Get semantic neighbors (most similar content) for a content source."""

        try:
            embedding = await self._generate_content_embedding(content_source)

            if not embedding:
                return []

            neighbors = await self.semantic_search.find_similar_content(
                db, embedding, limit=max_neighbors, similarity_threshold=0.5
            )

            # Format neighbor results
            formatted_neighbors = []
            for neighbor in neighbors:
                formatted_neighbors.append({
                    "content_source_id": neighbor.get('id'),
                    "similarity_score": neighbor.get('similarity', 0.0),
                    "title": neighbor.get('title', 'Unknown'),
                    "content_type": neighbor.get('source_type', 'unknown'),
                    "url": neighbor.get('url', '')
                })

            return formatted_neighbors

        except Exception as e:
            logger.error(f"Failed to get semantic neighbors for content source {content_source.id}: {e}")
            return []
