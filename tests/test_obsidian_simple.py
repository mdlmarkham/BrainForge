"""Simple integration tests for Obsidian Local REST API service."""

import pytest
import pytest_asyncio

from src.services.obsidian import (
    ObsidianCommand,
    ObsidianNote,
    ObsidianServerInfo,
    ObsidianService,
)


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


class TestObsidianServiceSimple:
    """Simple test cases for ObsidianService."""

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
            # Client should be properly initialized
            assert hasattr(obsidian_service.client, 'get')
            assert hasattr(obsidian_service.client, 'post')

    @pytest.mark.asyncio
    async def test_connection_failure(self, obsidian_service):
        """Test connection failure handling."""
        # This should fail gracefully when Obsidian API is not running
        async with obsidian_service:
            try:
                await obsidian_service.get_server_info()
                # If we get here, the test server might be running
                # This is acceptable for integration testing
                pass
            except Exception as e:
                # Expected behavior when Obsidian API is not available
                # Accept various connection-related errors
                error_msg = str(e).lower()
                assert any(keyword in error_msg for keyword in [
                    "connection", "timeout", "refused", "disconnected", "protocol"
                ])


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


@pytest.mark.asyncio
async def test_obsidian_api_routes_import():
    """Test that Obsidian API routes can be imported."""
    # This tests that the API routes are properly structured
    # Skip database-dependent imports for now
    try:
        from src.api.routes.obsidian import router
        assert router is not None
    except ImportError as e:
        pytest.fail(f"Failed to import Obsidian API routes: {e}")


@pytest.mark.asyncio
async def test_obsidian_cli_import():
    """Test that Obsidian CLI can be imported."""
    # This tests that the CLI is properly structured
    try:
        from src.cli.obsidian import main
        assert main is not None
    except ImportError as e:
        pytest.fail(f"Failed to import Obsidian CLI: {e}")
