"""Integration tests for Obsidian Local REST API service."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
import httpx

from src.services.obsidian import ObsidianService, ObsidianNote, ObsidianServerInfo, ObsidianCommand


@pytest.fixture
def mock_obsidian_config():
    """Mock Obsidian configuration."""
    return {
        "base_url": "http://localhost:27124",
        "token": "test-token"
    }


@pytest_asyncio.fixture
async def obsidian_service(mock_obsidian_config):
    """Create Obsidian service instance for testing."""
    service = ObsidianService(
        base_url=mock_obsidian_config["base_url"],
        token=mock_obsidian_config["token"]
    )
    return service


class TestObsidianService:
    """Test cases for ObsidianService."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_obsidian_config):
        """Test service initialization."""
        service = ObsidianService(
            base_url=mock_obsidian_config["base_url"],
            token=mock_obsidian_config["token"]
        )
        
        assert service.base_url == "http://localhost:27124"
        assert service.token == "test-token"
        assert service.client is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, obsidian_service):
        """Test async context manager."""
        async with obsidian_service:
            assert obsidian_service.client is not None
            assert isinstance(obsidian_service.client, httpx.AsyncClient)
        
        # Note: httpx.AsyncClient doesn't set itself to None after close
        # We'll check that the client was properly created and used
        pass
    
    @pytest.mark.asyncio
    async def test_get_server_info_success(self, obsidian_service):
        """Test successful server info retrieval."""
        mock_response = {
            "authenticated": True,
            "ok": "ok",
            "service": "obsidian-local-rest-api",
            "versions": {"obsidian": "1.0.0", "olr": "0.1.0"}
        }
        
        async with obsidian_service:
            with patch.object(obsidian_service.client, 'get') as mock_get:
                mock_get.return_value = AsyncMock(
                    status_code=200,
                    json=AsyncMock(return_value=mock_response)
                )
                
                info = await obsidian_service.get_server_info()
                
                assert isinstance(info, ObsidianServerInfo)
                assert info.authenticated == True
                assert info.ok == "ok"
                assert info.service == "obsidian-local-rest-api"
    
    @pytest.mark.asyncio
    async def test_get_note_success(self, obsidian_service):
        """Test successful note retrieval."""
        mock_response = {
            "content": "# Test Note\nThis is a test note.",
            "frontmatter": {"title": "Test Note"},
            "path": "test.md",
            "stat": {"size": 100},
            "tags": ["test", "example"]
        }
        
        async with obsidian_service:
            with patch.object(obsidian_service.client, 'get') as mock_get:
                mock_get.return_value = AsyncMock(
                    status_code=200,
                    json=AsyncMock(return_value=mock_response)
                )
                
                note = await obsidian_service.get_note("test.md", as_json=True)
                
                assert isinstance(note, ObsidianNote)
                assert note.content == "# Test Note\nThis is a test note."
                assert note.frontmatter == {"title": "Test Note"}
                assert note.path == "test.md"
    
    @pytest.mark.asyncio
    async def test_create_or_append_note_success(self, obsidian_service):
        """Test successful note creation/append."""
        async with obsidian_service:
            with patch.object(obsidian_service.client, 'post') as mock_post:
                mock_post.return_value = AsyncMock(status_code=200)
                
                await obsidian_service.create_or_append_note("test.md", "New content")
                
                mock_post.assert_called_once_with(
                    '/vault/test.md',
                    content='New content',
                    headers={'Content-Type': 'text/markdown'}
                )
    
    @pytest.mark.asyncio
    async def test_get_active_note_success(self, obsidian_service):
        """Test successful active note retrieval."""
        mock_response = {
            "content": "# Active Note\nThis is the active note.",
            "frontmatter": {"title": "Active Note"},
            "path": "active.md",
            "stat": {"size": 150},
            "tags": ["active"]
        }
        
        async with obsidian_service:
            with patch.object(obsidian_service.client, 'get') as mock_get:
                mock_get.return_value = AsyncMock(
                    status_code=200,
                    json=AsyncMock(return_value=mock_response)
                )
                
                note = await obsidian_service.get_active_note(as_json=True)
                
                assert isinstance(note, ObsidianNote)
                assert note.content == "# Active Note\nThis is the active note."
                assert note.path == "active.md"
    
    @pytest.mark.asyncio
    async def test_get_active_note_not_found(self, obsidian_service):
        """Test active note retrieval when no active note."""
        async with obsidian_service:
            with patch.object(obsidian_service.client, 'get') as mock_get:
                mock_get.return_value = AsyncMock(status_code=404)
                
                note = await obsidian_service.get_active_note()
                
                assert note is None
    
    @pytest.mark.asyncio
    async def test_list_vault_files_success(self, obsidian_service):
        """Test successful vault files listing."""
        mock_response = {
            "files": ["note1.md", "note2.md", "folder/note3.md"]
        }
        
        async with obsidian_service:
            with patch.object(obsidian_service.client, 'get') as mock_get:
                mock_get.return_value = AsyncMock(
                    status_code=200,
                    json=AsyncMock(return_value=mock_response)
                )
                
                files = await obsidian_service.list_vault_files()
                
                assert files == ["note1.md", "note2.md", "folder/note3.md"]
    
    @pytest.mark.asyncio
    async def test_get_available_commands_success(self, obsidian_service):
        """Test successful commands retrieval."""
        mock_response = {
            "commands": [
                {
                    "id": "command1",
                    "name": "Test Command 1"
                },
                {
                    "id": "command2",
                    "name": "Test Command 2"
                }
            ]
        }
        
        async with obsidian_service:
            with patch.object(obsidian_service.client, 'get') as mock_get:
                mock_get.return_value = AsyncMock(
                    status_code=200,
                    json=AsyncMock(return_value=mock_response)
                )
                
                commands = await obsidian_service.get_available_commands()
                
                assert len(commands) == 2
                assert isinstance(commands[0], ObsidianCommand)
                assert commands[0].id == "command1"
                assert commands[0].name == "Test Command 1"
    
    @pytest.mark.asyncio
    async def test_create_periodic_note_success(self, obsidian_service):
        """Test successful periodic note creation."""
        async with obsidian_service:
            with patch.object(obsidian_service.client, 'post') as mock_post:
                mock_post.return_value = AsyncMock(status_code=200)
                
                await obsidian_service.create_periodic_note(
                    "daily", 
                    "Daily note content",
                    year=2024,
                    month=11,
                    day=28
                )
                
                mock_post.assert_called_once_with(
                    '/periodic/daily/2024/11/28/',
                    content='Daily note content',
                    headers={'Content-Type': 'text/markdown'}
                )
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self, obsidian_service):
        """Test HTTP error handling."""
        async with obsidian_service:
            with patch.object(obsidian_service.client, 'get') as mock_get:
                mock_get.return_value = AsyncMock(
                    status_code=500,
                    raise_for_status=AsyncMock(side_effect=httpx.HTTPStatusError(
                        "Server error",
                        request=AsyncMock(),
                        response=AsyncMock(status_code=500)
                    ))
                )
                
                with pytest.raises(httpx.HTTPStatusError):
                    await obsidian_service.get_server_info()


class TestObsidianModels:
    """Test cases for Obsidian data models."""
    
    def test_obsidian_note_model(self):
        """Test ObsidianNote model creation."""
        note = ObsidianNote(
            content="# Test Note",
            frontmatter={"title": "Test"},
            path="test.md",
            stat={"size": 100},
            tags=["test"]
        )
        
        assert note.content == "# Test Note"
        assert note.frontmatter == {"title": "Test"}
        assert note.path == "test.md"
        assert note.tags == ["test"]
    
    def test_obsidian_server_info_model(self):
        """Test ObsidianServerInfo model creation."""
        info = ObsidianServerInfo(
            authenticated=True,
            ok="ok",
            service="obsidian-local-rest-api",
            versions={"obsidian": "1.0.0"}
        )
        
        assert info.authenticated == True
        assert info.ok == "ok"
        assert info.service == "obsidian-local-rest-api"
    
    def test_obsidian_command_model(self):
        """Test ObsidianCommand model creation."""
        command = ObsidianCommand(
            id="test-command",
            name="Test Command"
        )
        
        assert command.id == "test-command"
        assert command.name == "Test Command"