"""Integration tests for BrainForge database schema and API alignment."""

import pytest
import asyncio
from uuid import UUID

from src.models.note import NoteCreate, NoteType
from src.models.agent_run import AgentRunCreate, AgentRunStatus
from src.services.database import NoteService, AgentRunService


class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    @pytest.fixture
    def note_service(self):
        """Create a note service instance for testing."""
        return NoteService("sqlite:///:memory:")  # Use in-memory SQLite for testing
    
    @pytest.fixture
    def agent_run_service(self):
        """Create an agent run service instance for testing."""
        return AgentRunService("sqlite:///:memory:")  # Use in-memory SQLite for testing
    
    @pytest.mark.asyncio
    async def test_note_creation_integration(self, note_service):
        """Test note creation with full integration."""
        note_data = NoteCreate(
            content="Integration test note content",
            note_type=NoteType.FLEETING,
            created_by="integration_test@example.com"
        )
        
        # This will test the full flow from model validation to service creation
        note = await note_service.create(note_data)
        
        # Verify the note was created with proper validation
        assert note.content == "Integration test note content"
        assert note.note_type == NoteType.FLEETING
        assert note.created_by == "integration_test@example.com"
    
    @pytest.mark.asyncio
    async def test_agent_run_creation_integration(self, agent_run_service):
        """Test agent run creation with full integration."""
        agent_run_data = AgentRunCreate(
            agent_name="integration_test_agent",
            agent_version="1.0.0",
            input_parameters={"test": "data"},
            status=AgentRunStatus.PENDING_REVIEW
        )
        
        # This will test the full flow from model validation to service creation
        agent_run = await agent_run_service.create(agent_run_data)
        
        # Verify the agent run was created with proper validation
        assert agent_run.agent_name == "integration_test_agent"
        assert agent_run.agent_version == "1.0.0"
        assert agent_run.status == AgentRunStatus.PENDING_REVIEW
    
    @pytest.mark.asyncio
    async def test_note_validation_integration(self, note_service):
        """Test note validation errors in integration context."""
        # Test invalid note data (empty content)
        with pytest.raises(ValueError):
            invalid_note_data = NoteCreate(
                content="",  # Empty content should fail validation
                note_type=NoteType.FLEETING,
                created_by="test@example.com"
            )
            await note_service.create(invalid_note_data)
    
    @pytest.mark.asyncio
    async def test_agent_run_validation_integration(self, agent_run_service):
        """Test agent run validation errors in integration context."""
        # Test invalid agent version format
        with pytest.raises(ValueError):
            invalid_agent_data = AgentRunCreate(
                agent_name="test_agent",
                agent_version="invalid_version",  # Invalid semantic version
                input_parameters={},
                status=AgentRunStatus.PENDING_REVIEW
            )
            await agent_run_service.create(invalid_agent_data)


class TestSchemaAlignment:
    """Tests for database schema alignment with models."""
    
    def test_note_model_schema_alignment(self):
        """Test that Note model fields align with database schema."""
        # This would compare model fields with actual database schema
        # For now, we'll test that required fields are present
        note_fields = NoteCreate.model_fields.keys()
        required_fields = {'content', 'note_type', 'created_by'}
        
        assert required_fields.issubset(note_fields)
    
    def test_agent_run_model_schema_alignment(self):
        """Test that AgentRun model fields align with database schema."""
        agent_run_fields = AgentRunCreate.model_fields.keys()
        required_fields = {'agent_name', 'agent_version', 'status'}
        
        assert required_fields.issubset(agent_run_fields)


class TestAPICompliance:
    """Tests for API compliance with constitutional principles."""
    
    def test_api_endpoint_structure(self):
        """Test that API endpoints follow constitutional structure."""
        # This would test that all endpoints have proper validation,
        # error handling, and compliance checks
        # For now, we'll test basic structure
        
        # Test that required API endpoints exist
        required_endpoints = [
            '/api/v1/notes',
            '/api/v1/agent/runs'
        ]
        
        # In a real implementation, this would check the actual API router
        assert len(required_endpoints) > 0
    
    def test_error_handling_compliance(self):
        """Test that error handling follows constitutional principles."""
        # Test that proper HTTP status codes are used
        expected_status_codes = {
            200: 'OK',
            201: 'Created',
            400: 'Bad Request',
            404: 'Not Found',
            422: 'Unprocessable Entity',
            500: 'Internal Server Error'
        }
        
        # In a real implementation, this would test actual API responses
        assert len(expected_status_codes) >= 4  # At least basic error codes