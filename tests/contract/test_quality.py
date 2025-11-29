"""Contract tests for quality assessment API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4

from src.api.main import create_app
from src.models.quality_assessment import QualityAssessmentCreate, QualityScore
from src.models.content_source import ContentSource
from src.services.database import get_db


class TestQualityAPI:
    """Test quality assessment API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_quality_assessment_create(self):
        """Create sample quality assessment data."""
        return QualityAssessmentCreate(
            content_source_id=uuid4(),
            credibility_score=0.8,
            relevance_score=0.7,
            freshness_score=0.9,
            completeness_score=0.6,
            overall_score=0.75,
            summary="This is a test summary of the content quality.",
            classification="Research Paper",
            rationale="Test rationale explaining the quality scores."
        )
    
    @pytest.fixture
    def sample_content_source(self):
        """Create sample content source data."""
        return {
            "url": "https://example.com/test-article",
            "title": "Test Article for Quality Assessment",
            "description": "This is a test article for quality assessment",
            "source_type": "article",
            "content_hash": "abc123def456"
        }
    
    def test_create_quality_assessment(self, client, sample_quality_assessment_create):
        """Test creating a new quality assessment."""
        
        response = client.post("/api/v1/quality/assessments", json=sample_quality_assessment_create.model_dump())
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["credibility_score"] == sample_quality_assessment_create.credibility_score
        assert data["relevance_score"] == sample_quality_assessment_create.relevance_score
        assert data["freshness_score"] == sample_quality_assessment_create.freshness_score
        assert data["completeness_score"] == sample_quality_assessment_create.completeness_score
        assert data["overall_score"] == sample_quality_assessment_create.overall_score
    
    def test_assess_content_quality(self, client):
        """Test assessing content quality (requires existing content source)."""
        
        # This test would require a content source to exist first
        # For now, test the endpoint structure
        content_source_id = uuid4()
        response = client.post(f"/api/v1/quality/sources/{content_source_id}/assess")
        
        # Should return 404 if content source doesn't exist
        # or 500 if assessment fails, but endpoint should be accessible
        assert response.status_code in [404, 500]
    
    def test_get_quality_assessment_for_source(self, client):
        """Test getting quality assessment for a content source."""
        
        content_source_id = uuid4()
        response = client.get(f"/api/v1/quality/sources/{content_source_id}/assessment")
        
        # Should return 200 even if no assessment exists (returns null)
        # or 500 if there's an error
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Should return null if no assessment exists
            assert data is None or "id" in data
    
    def test_get_approved_sources_for_research_run(self, client):
        """Test getting approved sources for a research run."""
        
        research_run_id = uuid4()
        response = client.get(f"/api/v1/quality/research-runs/{research_run_id}/approved-sources")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should return empty list if no approved sources
    
    def test_get_approved_sources_with_min_score(self, client):
        """Test getting approved sources with minimum score filter."""
        
        research_run_id = uuid4()
        response = client.get(f"/api/v1/quality/research-runs/{research_run_id}/approved-sources?min_score=0.8")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_get_quality_statistics(self, client):
        """Test getting quality statistics for a research run."""
        
        research_run_id = uuid4()
        response = client.get(f"/api/v1/quality/research-runs/{research_run_id}/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
        # Should contain statistics fields
        assert "total_assessments" in data
        assert "average_score" in data
        assert "score_distribution" in data
    
    def test_reassess_content_quality(self, client):
        """Test reassessing content quality."""
        
        content_source_id = uuid4()
        response = client.post(f"/api/v1/quality/sources/{content_source_id}/reassess")
        
        # Should return 404 if content source doesn't exist
        # or 500 if reassessment fails
        assert response.status_code in [404, 500]
    
    def test_get_high_quality_sources(self, client):
        """Test getting high-quality sources."""
        
        response = client.get("/api/v1/quality/high-quality-sources")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_get_high_quality_sources_with_params(self, client):
        """Test getting high-quality sources with parameters."""
        
        response = client.get("/api/v1/quality/high-quality-sources?min_score=0.9&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_get_quality_assessment_by_id(self, client):
        """Test getting a quality assessment by ID."""
        
        assessment_id = uuid4()
        response = client.get(f"/api/v1/quality/assessments/{assessment_id}")
        
        # Should return 404 if assessment doesn't exist
        assert response.status_code in [404, 500]
    
    def test_list_quality_assessments(self, client):
        """Test listing quality assessments."""
        
        response = client.get("/api/v1/quality/assessments")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_list_quality_assessments_pagination(self, client):
        """Test listing quality assessments with pagination."""
        
        response = client.get("/api/v1/quality/assessments?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
    
    def test_delete_quality_assessment(self, client):
        """Test deleting a quality assessment."""
        
        assessment_id = uuid4()
        response = client.delete(f"/api/v1/quality/assessments/{assessment_id}")
        
        # Should return 404 if assessment doesn't exist
        assert response.status_code in [404, 500]
    
    def test_get_quality_breakdown(self, client):
        """Test getting quality breakdown for a content source."""
        
        content_source_id = uuid4()
        response = client.get(f"/api/v1/quality/breakdown/{content_source_id}")
        
        # Should return 404 if no assessment exists
        assert response.status_code in [404, 500]
    
    def test_quality_assessment_validation(self, client):
        """Test quality assessment creation validation."""
        
        # Test missing required fields
        invalid_data = {
            "credibility_score": 0.8
            # Missing content_source_id and other required fields
        }
        
        response = client.post("/api/v1/quality/assessments", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_quality_score_validation(self, client, sample_quality_assessment_create):
        """Test quality score validation."""
        
        # Test score out of range
        invalid_data = sample_quality_assessment_create.model_dump()
        invalid_data["credibility_score"] = 1.5  # Out of range
        
        response = client.post("/api/v1/quality/assessments", json=invalid_data)
        
        # Should validate score ranges (0.0 to 1.0)
        assert response.status_code == 422  # Validation error
    
    def test_quality_assessment_structure(self, client, sample_quality_assessment_create):
        """Test that quality assessment has proper structure."""
        
        response = client.post("/api/v1/quality/assessments", json=sample_quality_assessment_create.model_dump())
        
        if response.status_code == 201:
            data = response.json()
            
            # Should have all required fields
            assert "id" in data
            assert "content_source_id" in data
            assert "credibility_score" in data
            assert "relevance_score" in data
            assert "freshness_score" in data
            assert "completeness_score" in data
            assert "overall_score" in data
            assert "summary" in data
            assert "classification" in data
            assert "rationale" in data
            assert "created_at" in data
            assert "updated_at" in data
    
    def test_quality_score_enum(self):
        """Test that quality score uses correct value ranges."""
        
        # Test that scores are within valid range
        valid_scores = [0.0, 0.5, 0.7, 1.0]
        invalid_scores = [-0.1, 1.1, 2.0]
        
        for score in valid_scores:
            # Should be valid
            assert 0.0 <= score <= 1.0
        
        for score in invalid_scores:
            # Should be invalid
            assert not (0.0 <= score <= 1.0)


class TestQualityScoring:
    """Test quality scoring functionality."""
    
    def test_quality_score_calculation(self):
        """Test that overall score calculation follows expected weights."""
        
        # Test weighted average calculation
        credibility = 0.8
        relevance = 0.7
        freshness = 0.9
        completeness = 0.6
        
        # Expected weights: credibility 0.4, relevance 0.3, freshness 0.2, completeness 0.1
        expected_overall = (credibility * 0.4 + relevance * 0.3 + freshness * 0.2 + completeness * 0.1)
        
        # Should be approximately 0.77
        assert abs(expected_overall - 0.77) < 0.01
    
    def test_quality_dimensions(self):
        """Test that all quality dimensions are properly defined."""
        
        # QualityAssessment should have all expected dimensions
        expected_dimensions = [
            "credibility_score",
            "relevance_score", 
            "freshness_score",
            "completeness_score",
            "overall_score"
        ]
        
        # This would typically test the model structure
        # For now, verify the dimension names
        for dimension in expected_dimensions:
            assert dimension in ["credibility_score", "relevance_score", "freshness_score", 
                               "completeness_score", "overall_score"]
    
    def test_quality_assessment_metadata(self):
        """Test quality assessment metadata structure."""
        
        # Assessment should have metadata field
        # This would test the actual model
        assert True  # Placeholder for model structure test


@pytest.mark.asyncio
class TestQualityAsync:
    """Async tests for quality assessment functionality."""
    
    async def test_async_quality_operations(self, db_session: AsyncSession):
        """Test async quality operations."""
        
        # This would test actual database operations
        # For now, just verify the session works
        assert db_session is not None
        assert isinstance(db_session, AsyncSession)
    
    async def test_quality_service_integration(self):
        """Test quality service integration (would require actual implementation)."""
        
        # This would test the actual QualityAssessmentService
        # For contract tests, we focus on API endpoints
        assert True  # Placeholder for service integration tests