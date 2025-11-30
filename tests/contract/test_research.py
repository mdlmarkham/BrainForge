"""Contract tests for research API endpoints."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import create_app
from src.models.content_source import ContentSource
from src.models.research_run import ResearchRunCreate, ResearchRunStatus


class TestResearchAPI:
    """Test research API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def sample_research_run_create(self):
        """Create sample research run data."""
        return ResearchRunCreate(
            research_topic="Test Research Topic",
            created_by="test-user",
            research_parameters={
                "max_sources": 10,
                "sources": ["google", "semantic_scholar", "news"]
            }
        )

    @pytest.fixture
    def sample_content_source(self):
        """Create sample content source data."""
        return {
            "url": "https://example.com/test-article",
            "title": "Test Article",
            "description": "This is a test article for research",
            "source_type": "article",
            "content_hash": "abc123def456"
        }

    def test_create_research_run(self, client, sample_research_run_create):
        """Test creating a new research run."""

        response = client.post("/api/v1/research/runs", json=sample_research_run_create.model_dump())

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["research_topic"] == sample_research_run_create.research_topic
        assert data["created_by"] == sample_research_run_create.created_by
        assert data["status"] == ResearchRunStatus.PENDING.value

    def test_get_research_run(self, client, sample_research_run_create):
        """Test getting a specific research run."""

        # First create a research run
        create_response = client.post("/api/v1/research/runs", json=sample_research_run_create.model_dump())
        research_run_id = create_response.json()["id"]

        # Then get it
        response = client.get(f"/api/v1/research/runs/{research_run_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == research_run_id
        assert data["research_topic"] == sample_research_run_create.research_topic

    def test_get_nonexistent_research_run(self, client):
        """Test getting a research run that doesn't exist."""

        nonexistent_id = uuid4()
        response = client.get(f"/api/v1/research/runs/{nonexistent_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_research_runs(self, client, sample_research_run_create):
        """Test listing research runs."""

        # Create a research run first
        client.post("/api/v1/research/runs", json=sample_research_run_create.model_dump())

        response = client.get("/api/v1/research/runs")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "research_topic" in data[0]

    def test_list_research_runs_pagination(self, client, sample_research_run_create):
        """Test listing research runs with pagination."""

        response = client.get("/api/v1/research/runs?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should not error even with no data

    def test_start_research_run(self, client, sample_research_run_create):
        """Test starting a research run."""

        # First create a research run
        create_response = client.post("/api/v1/research/runs", json=sample_research_run_create.model_dump())
        research_run_id = create_response.json()["id"]

        # Then start it
        response = client.post(f"/api/v1/research/runs/{research_run_id}/start")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == research_run_id
        # Status should be updated (though actual workflow would run in background)

    def test_start_nonexistent_research_run(self, client):
        """Test starting a research run that doesn't exist."""

        nonexistent_id = uuid4()
        response = client.post(f"/api/v1/research/runs/{nonexistent_id}/start")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_research_run_sources(self, client, sample_research_run_create):
        """Test getting content sources for a research run."""

        # First create a research run
        create_response = client.post("/api/v1/research/runs", json=sample_research_run_create.model_dump())
        research_run_id = create_response.json()["id"]

        # Get sources (may be empty initially)
        response = client.get(f"/api/v1/research/runs/{research_run_id}/sources")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should return empty list if no sources yet

    def test_get_pending_research_runs(self, client):
        """Test getting pending research runs."""

        response = client.get("/api/v1/research/runs/pending")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should not error even with no pending runs

    def test_get_running_research_runs(self, client):
        """Test getting running research runs."""

        response = client.get("/api/v1/research/runs/running")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should not error even with no running runs

    def test_update_research_run(self, client, sample_research_run_create):
        """Test updating a research run."""

        # First create a research run
        create_response = client.post("/api/v1/research/runs", json=sample_research_run_create.model_dump())
        research_run_id = create_response.json()["id"]

        # Update it
        update_data = {
            "research_topic": "Updated Research Topic",
            "research_parameters": {
                "max_sources": 5,
                "sources": ["google"]
            }
        }

        response = client.put(f"/api/v1/research/runs/{research_run_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == research_run_id
        assert data["research_topic"] == "Updated Research Topic"

    def test_update_nonexistent_research_run(self, client):
        """Test updating a research run that doesn't exist."""

        nonexistent_id = uuid4()
        update_data = {"research_topic": "Updated Topic"}

        response = client.put(f"/api/v1/research/runs/{nonexistent_id}", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_research_run_validation(self, client):
        """Test research run creation validation."""

        # Test missing required fields
        invalid_data = {
            "created_by": "test-user"
            # Missing research_topic
        }

        response = client.post("/api/v1/research/runs", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_research_run_status_enum(self, client, sample_research_run_create):
        """Test that research run status uses correct enum values."""

        response = client.post("/api/v1/research/runs", json=sample_research_run_create.model_dump())

        assert response.status_code == 201
        data = response.json()

        # Status should be one of the valid enum values
        valid_statuses = [status.value for status in ResearchRunStatus]
        assert data["status"] in valid_statuses

    def test_research_run_timestamps(self, client, sample_research_run_create):
        """Test that research runs have proper timestamps."""

        response = client.post("/api/v1/research/runs", json=sample_research_run_create.model_dump())

        assert response.status_code == 201
        data = response.json()

        # Should have created_at timestamp
        assert "created_at" in data
        assert data["created_at"] is not None

        # Updated_at should be same as created_at initially
        assert "updated_at" in data
        assert data["updated_at"] == data["created_at"]


class TestResearchOrchestration:
    """Test research orchestration functionality."""

    def test_research_workflow_states(self):
        """Test that research workflow states are properly defined."""

        # ResearchRunStatus should have all expected states
        expected_states = [
            ResearchRunStatus.PENDING,
            ResearchRunStatus.RUNNING,
            ResearchRunStatus.COMPLETED,
            ResearchRunStatus.FAILED,
            ResearchRunStatus.CANCELLED
        ]

        for state in expected_states:
            assert state in ResearchRunStatus

    def test_content_source_validation(self):
        """Test content source model validation."""

        # Test valid content source
        valid_source = ContentSource(
            url="https://example.com/article",
            title="Test Article",
            description="Test description",
            source_type="article",
            content_hash="abc123"
        )

        assert valid_source.url == "https://example.com/article"
        assert valid_source.title == "Test Article"

        # Test URL validation (would be handled by Pydantic)
        # This is more of a model-level test


@pytest.mark.asyncio
class TestResearchAsync:
    """Async tests for research functionality."""

    async def test_async_research_operations(self, db_session: AsyncSession):
        """Test async research operations."""

        # This would test actual database operations
        # For now, just verify the session works
        assert db_session is not None
        assert isinstance(db_session, AsyncSession)
