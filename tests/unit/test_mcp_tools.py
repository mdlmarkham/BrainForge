"""Unit tests for MCP tools"""

import pytest
from unittest.mock import Mock, AsyncMock
from uuid import UUID, uuid4

from src.mcp.tools.search import SearchTools
from src.mcp.tools.notes import NoteTools
from src.mcp.tools.workflows import WorkflowTools
from src.mcp.tools.export import ExportTools


class TestSearchTools:
    """Test search tools functionality"""
    
    @pytest.fixture
    def search_tools(self):
        db_service = Mock()
        return SearchTools(db_service)
    
    @pytest.mark.asyncio
    async def test_search_library(self, search_tools):
        """Test basic search functionality"""
        # Mock the search service
        search_tools.search_service.search_notes = AsyncMock(return_value=[])
        
        result = await search_tools.search_library("test query")
        
        assert "query" in result
        assert "total_results" in result
        assert result["query"] == "test query"
    
    @pytest.mark.asyncio
    async def test_get_library_stats(self, search_tools):
        """Test library statistics"""
        # Mock database service
        search_tools.database_service.count = AsyncMock(return_value=10)
        search_tools.database_service.get_all = AsyncMock(return_value=[])
        
        result = await search_tools.get_library_stats()
        
        assert "total_notes" in result
        assert "total_links" in result


class TestNoteTools:
    """Test note management tools"""
    
    @pytest.fixture
    def note_tools(self):
        db_service = Mock()
        return NoteTools(db_service)
    
    @pytest.mark.asyncio
    async def test_create_note(self, note_tools):
        """Test note creation"""
        # Mock database service
        mock_note = Mock()
        mock_note.id = uuid4()
        mock_note.title = "Test Note"
        mock_note.content = "Test content"
        mock_note.tags = []
        mock_note.created_at = None
        
        note_tools.database_service.create = AsyncMock(return_value=mock_note)
        note_tools.search_service.index_note = AsyncMock()
        
        result = await note_tools.create_note("Test Note", "Test content")
        
        assert "note_id" in result
        assert result["title"] == "Test Note"
        assert result["status"] == "created"
    
    @pytest.mark.asyncio
    async def test_get_note(self, note_tools):
        """Test note retrieval"""
        # Mock database service
        mock_note = Mock()
        mock_note.id = uuid4()
        mock_note.title = "Test Note"
        mock_note.content = "Test content"
        mock_note.tags = []
        mock_note.source = None
        mock_note.created_at = None
        mock_note.updated_at = None
        
        note_tools.database_service.get_by_id = AsyncMock(return_value=mock_note)
        
        result = await note_tools.get_note(uuid4())
        
        assert "note_id" in result
        assert result["title"] == "Test Note"
        assert result["status"] == "found"


class TestWorkflowTools:
    """Test workflow tools"""
    
    @pytest.fixture
    def workflow_tools(self):
        db_service = Mock()
        workflow_orchestrator = Mock()
        return WorkflowTools(db_service, workflow_orchestrator)
    
    @pytest.mark.asyncio
    async def test_start_workflow(self, workflow_tools):
        """Test workflow start"""
        # Mock database service and orchestrator
        mock_workflow = Mock()
        mock_workflow.id = uuid4()
        
        workflow_tools.database_service.create = AsyncMock(return_value=mock_workflow)
        workflow_tools.workflow_orchestrator.start_workflow = AsyncMock(
            return_value={"status": "started", "current_step": "initializing", "progress": 0.1}
        )
        
        result = await workflow_tools.start_research_workflow("research_discovery")
        
        assert "workflow_id" in result
        assert result["status"] == "started"


class TestExportTools:
    """Test export tools"""
    
    @pytest.fixture
    def export_tools(self):
        db_service = Mock()
        return ExportTools(db_service)
    
    @pytest.mark.asyncio
    async def test_export_library(self, export_tools):
        """Test library export"""
        # Mock database service
        export_tools.database_service.get_all = AsyncMock(return_value=[])
        export_tools.database_service.count = AsyncMock(return_value=0)
        
        result = await export_tools.export_library("json")
        
        assert "format" in result
        assert "content" in result
        assert result["format"] == "json"
    
    @pytest.mark.asyncio
    async def test_generate_documentation(self, export_tools):
        """Test documentation generation"""
        # Mock database service
        export_tools.database_service.count = AsyncMock(return_value=0)
        export_tools.database_service.get_all = AsyncMock(return_value=[])
        
        result = await export_tools.generate_documentation()
        
        assert "output_format" in result
        assert "documentation" in result
        assert result["output_format"] == "markdown"


if __name__ == "__main__":
    pytest.main([__file__])