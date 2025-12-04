"""Unit tests for semantic search service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.note import Note, NoteType
from src.services.semantic_search import SemanticSearch


class TestSemanticSearch:
    """Test semantic search service functionality."""

    @pytest.fixture
    def semantic_search(self):
        """Create a semantic search service instance."""
        mock_embedding_service = MagicMock()
        mock_vector_store = MagicMock()
        mock_note_service = MagicMock()
        
        return SemanticSearch(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            note_service=mock_note_service
        )

    @pytest.fixture
    def mock_note(self):
        """Create a mock note for testing."""
        return Note(
            id=uuid4(),
            content="Test note content about artificial intelligence and machine learning",
            note_type=NoteType.PERMANENT,
            created_by="test@example.com",
            version=1
        )

    @pytest.mark.asyncio
    async def test_semantic_search_basic_functionality(self, semantic_search):
        """Test basic semantic search functionality."""
        # Mock dependencies
        semantic_search.embedding_service.generate_embedding.return_value = [0.1] * 384
        semantic_search.vector_store.search_similar.return_value = [
            {"note_id": str(uuid4()), "similarity": 0.85}
        ]
        semantic_search.note_service.get_by_id.return_value = self.mock_note()

        # Perform search
        query = "artificial intelligence"
        results = await semantic_search.semantic_search(query)

        # Verify results
        assert len(results) == 1
        assert results[0]["similarity"] == 0.85
        semantic_search.embedding_service.generate_embedding.assert_called_once_with(query)
        semantic_search.vector_store.search_similar.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_search_with_filters(self, semantic_search):
        """Test semantic search with metadata filters."""
        # Mock dependencies
        semantic_search.embedding_service.generate_embedding.return_value = [0.1] * 384
        semantic_search.vector_store.search_similar.return_value = [
            {"note_id": str(uuid4()), "similarity": 0.90}
        ]
        semantic_search.note_service.get_by_id.return_value = self.mock_note()

        # Perform search with filters
        query = "machine learning"
        filters = {"note_type": "permanent", "tags": ["ai"]}
        results = await semantic_search.semantic_search(query, filters=filters)

        # Verify filters were applied
        assert len(results) == 1
        semantic_search.vector_store.search_similar.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_search_with_limit(self, semantic_search):
        """Test semantic search with result limit."""
        # Mock multiple results
        semantic_search.embedding_service.generate_embedding.return_value = [0.1] * 384
        semantic_search.vector_store.search_similar.return_value = [
            {"note_id": str(uuid4()), "similarity": 0.85},
            {"note_id": str(uuid4()), "similarity": 0.80},
            {"note_id": str(uuid4()), "similarity": 0.75}
        ]
        semantic_search.note_service.get_by_id.return_value = self.mock_note()

        # Perform search with limit
        query = "test query"
        results = await semantic_search.semantic_search(query, limit=2)

        # Verify limit was applied
        assert len(results) == 2
        assert results[0]["similarity"] == 0.85
        assert results[1]["similarity"] == 0.80

    @pytest.mark.asyncio
    async def test_semantic_search_with_similarity_threshold(self, semantic_search):
        """Test semantic search with similarity threshold."""
        # Mock results with varying similarities
        semantic_search.embedding_service.generate_embedding.return_value = [0.1] * 384
        semantic_search.vector_store.search_similar.return_value = [
            {"note_id": str(uuid4()), "similarity": 0.90},
            {"note_id": str(uuid4()), "similarity": 0.70},
            {"note_id": str(uuid4()), "similarity": 0.50}
        ]
        semantic_search.note_service.get_by_id.return_value = self.mock_note()

        # Perform search with threshold
        query = "test query"
        results = await semantic_search.semantic_search(query, similarity_threshold=0.75)

        # Verify threshold was applied
        assert len(results) == 1
        assert results[0]["similarity"] == 0.90

    @pytest.mark.asyncio
    async def test_hybrid_search_combination(self, semantic_search):
        """Test hybrid search combining semantic and metadata relevance."""
        # Mock both semantic and metadata scoring
        semantic_search.embedding_service.generate_embedding.return_value = [0.1] * 384
        semantic_search.vector_store.search_similar.return_value = [
            {"note_id": str(uuid4()), "similarity": 0.85}
        ]
        semantic_search.note_service.get_by_id.return_value = self.mock_note()

        # Perform hybrid search
        query = "test query"
        weights = {"semantic": 0.7, "metadata": 0.3}
        results = await semantic_search.hybrid_search(query, weights=weights)

        # Verify hybrid search was performed
        assert len(results) == 1
        semantic_search.embedding_service.generate_embedding.assert_called_once_with(query)

    @pytest.mark.asyncio
    async def test_search_error_handling(self, semantic_search):
        """Test error handling during search operations."""
        # Mock embedding service failure
        semantic_search.embedding_service.generate_embedding.side_effect = Exception("Embedding service unavailable")

        # Perform search that should fail
        query = "test query"
        
        with pytest.raises(Exception, match="Embedding service unavailable"):
            await semantic_search.semantic_search(query)

    @pytest.mark.asyncio
    async def test_empty_query_validation(self, semantic_search):
        """Test validation of empty queries."""
        # Test empty query
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await semantic_search.semantic_search("")

        # Test whitespace-only query
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await semantic_search.semantic_search("   ")

    @pytest.mark.asyncio
    async def test_search_audit_logging(self, semantic_search):
        """Test that search operations are logged for audit."""
        # Mock dependencies
        semantic_search.embedding_service.generate_embedding.return_value = [0.1] * 384
        semantic_search.vector_store.search_similar.return_value = [
            {"note_id": str(uuid4()), "similarity": 0.85}
        ]
        semantic_search.note_service.get_by_id.return_value = self.mock_note()

        # Mock audit service
        mock_audit_service = MagicMock()
        semantic_search.audit_service = mock_audit_service

        # Perform search
        query = "test query"
        results = await semantic_search.semantic_search(query)

        # Verify audit logging
        mock_audit_service.log_search.assert_called_once_with(query, len(results))

    def mock_note(self):
        """Helper method to create a mock note."""
        return Note(
            id=uuid4(),
            content="Test note content",
            note_type=NoteType.PERMANENT,
            created_by="test@example.com",
            version=1
        )


class TestSearchScoring:
    """Test search scoring algorithms."""

    @pytest.fixture
    def semantic_search(self):
        """Create a semantic search service instance."""
        mock_embedding_service = MagicMock()
        mock_vector_store = MagicMock()
        mock_note_service = MagicMock()
        
        return SemanticSearch(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            note_service=mock_note_service
        )

    def test_cosine_similarity_calculation(self, semantic_search):
        """Test cosine similarity calculation between vectors."""
        # Test identical vectors
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]
        similarity = semantic_search._calculate_cosine_similarity(vector1, vector2)
        assert similarity == 1.0

        # Test orthogonal vectors
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [0.0, 1.0, 0.0]
        similarity = semantic_search._calculate_cosine_similarity(vector1, vector2)
        assert similarity == 0.0

        # Test opposite vectors
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [-1.0, 0.0, 0.0]
        similarity = semantic_search._calculate_cosine_similarity(vector1, vector2)
        assert similarity == -1.0

    def test_metadata_score_calculation(self, semantic_search):
        """Test metadata relevance score calculation."""
        # Test exact match
        note_metadata = {"tags": ["ai", "machine-learning"], "note_type": "permanent"}
        search_filters = {"tags": ["ai"], "note_type": "permanent"}
        score = semantic_search._calculate_metadata_score(note_metadata, search_filters)
        assert 0.8 <= score <= 1.0  # Should be high for exact match

        # Test partial match
        note_metadata = {"tags": ["ai", "machine-learning"], "note_type": "permanent"}
        search_filters = {"tags": ["python"]}  # No matching tags
        score = semantic_search._calculate_metadata_score(note_metadata, search_filters)
        assert 0.0 <= score <= 0.5  # Should be low for no match

        # Test no filters (should return neutral score)
        note_metadata = {"tags": ["ai"], "note_type": "permanent"}
        search_filters = {}
        score = semantic_search._calculate_metadata_score(note_metadata, search_filters)
        assert score == 0.5  # Neutral score when no filters

    def test_hybrid_score_combination(self, semantic_search):
        """Test hybrid score combination algorithm."""
        # Test weighted combination
        semantic_score = 0.85
        metadata_score = 0.90
        weights = {"semantic": 0.7, "metadata": 0.3}
        
        hybrid_score = semantic_search._combine_hybrid_score(semantic_score, metadata_score, weights)
        
        expected_score = (0.85 * 0.7) + (0.90 * 0.3)
        assert hybrid_score == pytest.approx(expected_score, 0.01)

        # Test equal weights
        weights = {"semantic": 0.5, "metadata": 0.5}
        hybrid_score = semantic_search._combine_hybrid_score(semantic_score, metadata_score, weights)
        
        expected_score = (0.85 * 0.5) + (0.90 * 0.5)
        assert hybrid_score == pytest.approx(expected_score, 0.01)


class TestSearchPerformance:
    """Test search performance characteristics."""

    @pytest.fixture
    def semantic_search(self):
        """Create a semantic search service instance."""
        mock_embedding_service = MagicMock()
        mock_vector_store = MagicMock()
        mock_note_service = MagicMock()
        
        return SemanticSearch(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            note_service=mock_note_service
        )

    @pytest.mark.asyncio
    async def test_search_response_time(self, semantic_search):
        """Test search response time performance."""
        import time
        
        # Mock fast response
        semantic_search.embedding_service.generate_embedding.return_value = [0.1] * 384
        semantic_search.vector_store.search_similar.return_value = [{"note_id": str(uuid4()), "similarity": 0.85}]
        semantic_search.note_service.get_by_id.return_value = MagicMock()

        start_time = time.time()
        results = await semantic_search.semantic_search("test query")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify reasonable response time (under 500ms for basic search)
        assert response_time < 500
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self, semantic_search):
        """Test performance under concurrent search load."""
        import asyncio
        
        # Mock dependencies for concurrent testing
        semantic_search.embedding_service.generate_embedding.return_value = [0.1] * 384
        semantic_search.vector_store.search_similar.return_value = [{"note_id": str(uuid4()), "similarity": 0.85}]
        semantic_search.note_service.get_by_id.return_value = MagicMock()

        async def perform_search(query):
            return await semantic_search.semantic_search(query)

        # Perform concurrent searches
        queries = [f"query {i}" for i in range(5)]
        start_time = time.time()
        results = await asyncio.gather(*[perform_search(query) for query in queries])
        end_time = time.time()

        total_time = (end_time - start_time) * 1000
        
        # Verify all searches completed
        assert len(results) == 5
        assert total_time < 1000  # Should complete within 1 second for 5 concurrent searches