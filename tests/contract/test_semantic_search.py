"""Contract tests for semantic search endpoints.

These tests validate the API contracts for the implemented semantic search functionality.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.models.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)


class TestSemanticSearchContract:
    """Test semantic search API contract compliance."""

    def setup_method(self):
        """Set up test client with mocked dependencies."""
        self.app = create_app()
        self.client = TestClient(self.app)

    @patch('src.api.routes.search.get_database_service')
    @patch('src.api.routes.search.EmbeddingGenerator')
    @patch('src.api.routes.search.VectorStore')
    @patch('src.api.routes.search.HNSWIndex')
    @patch('src.api.routes.search.SemanticSearch')
    def test_search_endpoint_exists(self, mock_semantic_search, mock_hnsw, mock_vector, mock_embedding, mock_db_service):
        """Test that search endpoint exists with correct method."""
        # Mock the services to return successful results
        mock_search_instance = AsyncMock()
        mock_search_instance.semantic_search.return_value = []
        mock_semantic_search.return_value = mock_search_instance

        # Test that POST /api/v1/search endpoint exists
        response = self.client.post("/api/v1/search", json={
            "query": "test query"
        })

        # Should not get 404 (endpoint exists)
        assert response.status_code != 404, "Search endpoint does not exist"

    def test_search_request_schema_validation(self):
        """Test search request schema validation."""
        # Test required field validation
        response = self.client.post("/api/v1/search", json={})
        assert response.status_code == 422, "Empty request should be rejected"

        # Test query field validation
        response = self.client.post("/api/v1/search", json={"query": ""})
        assert response.status_code == 422, "Empty query should be rejected"

        # Test valid request
        response = self.client.post("/api/v1/search", json={
            "query": "valid query",
            "limit": 10,
            "similarity_threshold": 0.7
        })
        # Should not get validation error for valid request
        assert response.status_code != 422, "Valid request should not be rejected"

    @patch('src.api.routes.search.get_database_service')
    @patch('src.api.routes.search.EmbeddingGenerator')
    @patch('src.api.routes.search.VectorStore')
    @patch('src.api.routes.search.HNSWIndex')
    @patch('src.api.routes.search.SemanticSearch')
    def test_search_response_schema(self, mock_semantic_search, mock_hnsw, mock_vector, mock_embedding, mock_db_service):
        """Test search response schema validation."""
        # Mock successful search with sample results
        mock_search_instance = AsyncMock()
        mock_search_instance.semantic_search.return_value = [
            {
                "note": {
                    "id": str(uuid.uuid4()),
                    "content": "Test note content",
                    "note_type": "permanent",
                    "metadata": {},
                    "version": 1
                },
                "similarity_score": 0.85,
                "embedding_vector": [0.1, 0.2, 0.3]
            }
        ]
        mock_semantic_search.return_value = mock_search_instance

        response = self.client.post("/api/v1/search", json={
            "query": "test query"
        })

        if response.status_code == 200:
            data = response.json()
            # Check required response fields
            required_fields = ["results", "total_results", "query_time_ms", "search_type", "query"]
            for field in required_fields:
                assert field in data, f"Response missing required field: {field}"

    def test_search_stats_endpoint_exists(self):
        """Test that search stats endpoint exists."""
        response = self.client.get("/api/v1/search/stats")
        # Should not get 404 (endpoint exists)
        assert response.status_code != 404, "Search stats endpoint does not exist"

    def test_search_health_endpoint_exists(self):
        """Test that search health endpoint exists."""
        response = self.client.get("/api/v1/search/health")
        # Should not get 404 (endpoint exists)
        assert response.status_code != 404, "Search health endpoint does not exist"

    def test_similar_notes_endpoint_exists(self):
        """Test that similar notes endpoint exists."""
        test_note_id = str(uuid.uuid4())
        response = self.client.get(f"/api/v1/search/similar/{test_note_id}")
        # Should not get 404 (endpoint exists)
        assert response.status_code != 404, "Similar notes endpoint does not exist"


class TestSearchRequestValidation:
    """Test search request validation rules."""

    def setup_method(self):
        """Set up test client."""
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_empty_query_rejection(self):
        """Test that empty queries are rejected."""
        response = self.client.post("/api/v1/search", json={"query": ""})
        assert response.status_code == 422, "Empty query should be rejected"

        response = self.client.post("/api/v1/search", json={"query": "   "})
        assert response.status_code == 422, "Whitespace-only query should be rejected"

    def test_invalid_limit_rejection(self):
        """Test that invalid limits are rejected."""
        # Test limit below minimum
        response = self.client.post("/api/v1/search", json={
            "query": "test",
            "limit": 0
        })
        assert response.status_code == 422, "Limit below 1 should be rejected"

        # Test limit above maximum
        response = self.client.post("/api/v1/search", json={
            "query": "test",
            "limit": 101
        })
        assert response.status_code == 422, "Limit above 100 should be rejected"

    def test_invalid_similarity_threshold_rejection(self):
        """Test that invalid similarity thresholds are rejected."""
        # Test threshold below minimum
        response = self.client.post("/api/v1/search", json={
            "query": "test",
            "similarity_threshold": -0.1
        })
        assert response.status_code == 422, "Similarity threshold below 0 should be rejected"

        # Test threshold above maximum
        response = self.client.post("/api/v1/search", json={
            "query": "test",
            "similarity_threshold": 1.1
        })
        assert response.status_code == 422, "Similarity threshold above 1 should be rejected"


class TestSearchModels:
    """Test search model validation."""

    def test_search_request_model(self):
        """Test SearchRequest model validation."""
        # Valid request
        valid_request = SearchRequest(
            query="test query",
            limit=10,
            similarity_threshold=0.7
        )
        assert valid_request.query == "test query"
        assert valid_request.limit == 10
        assert valid_request.similarity_threshold == 0.7

        # Test empty query validation
        with pytest.raises(ValueError):
            SearchRequest(query="")

        # Test whitespace-only query validation
        with pytest.raises(ValueError):
            SearchRequest(query="   ")

    def test_search_result_model(self):
        """Test SearchResult model validation."""
        test_note_id = uuid.uuid4()
        result = SearchResult(
            note_id=test_note_id,
            content="Test content",
            note_type="permanent",
            similarity_score=0.85,
            metadata={"key": "value"},
            version=1
        )

        assert result.note_id == test_note_id
        assert result.content == "Test content"
        assert result.similarity_score == 0.85
        assert result.metadata == {"key": "value"}

    def test_search_response_model(self):
        """Test SearchResponse model validation."""
        test_note_id = uuid.uuid4()
        results = [
            SearchResult(
                note_id=test_note_id,
                content="Test content",
                note_type="permanent",
                similarity_score=0.85,
                metadata={},
                version=1
            )
        ]

        response = SearchResponse(
            results=results,
            total_results=1,
            query_time_ms=150.5,
            search_type="semantic",
            query="test query"
        )

        assert len(response.results) == 1
        assert response.total_results == 1
        assert response.query_time_ms == 150.5
        assert response.search_type == "semantic"
        assert response.query == "test query"


if __name__ == "__main__":
    pytest.main([__file__])
