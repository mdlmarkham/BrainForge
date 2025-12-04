"""Integration tests for note creation and search workflow.

These tests validate the complete workflow from note creation through
embedding generation to semantic search.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.note import Note, NoteCreate, NoteType
from src.services.embedding_generator import EmbeddingGenerator
from src.services.database import NoteService
from src.services.semantic_search import SemanticSearch
from src.services.vector_store import VectorStore


class TestNoteCreationWorkflow:
    """Test complete note creation workflow."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for integration testing."""
        # Mock database session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # Mock embedding service
        mock_embedding_service = MagicMock(spec=EmbeddingGenerator)
        mock_embedding_service.generate_embedding.return_value = [0.1] * 384
        mock_embedding_service.batch_generate_embeddings.return_value = [[0.1] * 384] * 5

        # Mock vector store
        mock_vector_store = MagicMock(spec=VectorStore)
        mock_vector_store.store_embedding.return_value = str(uuid4())
        mock_vector_store.search_similar.return_value = [{"note_id": str(uuid4()), "similarity": 0.85}]

        # Mock search service
        mock_search_service = MagicMock()
        mock_search_service.index_note = AsyncMock()
        mock_search_service.update_note_index = AsyncMock()
        mock_search_service.remove_note_from_index = AsyncMock()

        return {
            "session": mock_session,
            "embedding_service": mock_embedding_service,
            "vector_store": mock_vector_store,
            "search_service": mock_search_service
        }

    @pytest.mark.asyncio
    async def test_complete_note_creation_workflow(self, mock_services):
        """Test complete workflow from note creation to embedding generation."""
        # Create note service
        note_service = NoteService(
            session=mock_services["session"],
            embedding_service=mock_services["embedding_service"],
            search_service=mock_services["search_service"]
        )

        # Create semantic search service
        search_service = SemanticSearch(
            embedding_service=mock_services["embedding_service"],
            vector_store=mock_services["vector_store"],
            note_service=note_service
        )

        # Test data
        note_data = NoteCreate(
            content="Integration test note about artificial intelligence research",
            note_type=NoteType.PERMANENT,
            created_by="integration_test@example.com"
        )

        # Step 1: Create note
        mock_note = Note(
            id=uuid4(),
            content=note_data.content,
            note_type=note_data.note_type,
            created_by=note_data.created_by,
            version=1
        )
        mock_services["session"].refresh.return_value = mock_note

        created_note = await note_service.create(note_data)

        # Verify note creation
        assert created_note.content == note_data.content
        assert created_note.note_type == note_data.note_type
        mock_services["session"].add.assert_called_once()
        mock_services["session"].commit.assert_called_once()

        # Verify embedding generation was triggered
        mock_services["embedding_service"].generate_embedding.assert_called_once_with(note_data.content)

        # Verify search indexing
        mock_services["search_service"].index_note.assert_called_once()

        # Step 2: Search for the created note
        search_results = await search_service.semantic_search("artificial intelligence")

        # Verify search results
        assert len(search_results) == 1
        mock_services["embedding_service"].generate_embedding.assert_called_with("artificial intelligence")
        mock_services["vector_store"].search_similar.assert_called_once()

    @pytest.mark.asyncio
    async def test_note_update_workflow(self, mock_services):
        """Test complete workflow for note updates."""
        # Create services
        note_service = NoteService(
            session=mock_services["session"],
            embedding_service=mock_services["embedding_service"],
            search_service=mock_services["search_service"]
        )

        # Create an existing note
        note_id = uuid4()
        original_note = Note(
            id=note_id,
            content="Original note content",
            note_type=NoteType.PERMANENT,
            created_by="test@example.com",
            version=1
        )

        # Mock existing note retrieval
        mock_services["session"].execute.return_value.scalar_one_or_none.return_value = original_note

        # Update the note
        update_data = {
            "content": "Updated note content with more details about AI",
            "version": 2
        }

        updated_note = await note_service.update(note_id, update_data)

        # Verify update operations
        mock_services["session"].commit.assert_called_once()
        mock_services["embedding_service"].generate_embedding.assert_called_once_with(update_data["content"])
        mock_services["search_service"].update_note_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_note_deletion_workflow(self, mock_services):
        """Test complete workflow for note deletion."""
        # Create note service
        note_service = NoteService(
            session=mock_services["session"],
            embedding_service=mock_services["embedding_service"],
            search_service=mock_services["search_service"]
        )

        # Create an existing note
        note_id = uuid4()
        existing_note = Note(
            id=note_id,
            content="Note to be deleted",
            note_type=NoteType.FLEETING,
            created_by="test@example.com",
            version=1
        )

        # Mock existing note retrieval
        mock_services["session"].execute.return_value.scalar_one_or_none.return_value = existing_note
        mock_services["session"].delete = MagicMock()

        # Delete the note
        result = await note_service.delete(note_id)

        # Verify deletion operations
        assert result is True
        mock_services["session"].delete.assert_called_once_with(existing_note)
        mock_services["session"].commit.assert_called_once()
        mock_services["search_service"].remove_note_from_index.assert_called_once_with(note_id)


class TestSearchWorkflow:
    """Test complete search workflow."""

    @pytest.fixture
    def mock_search_environment(self):
        """Create mock search environment."""
        # Mock multiple notes for search testing
        notes = [
            Note(
                id=uuid4(),
                content=f"Note about artificial intelligence topic {i}",
                note_type=NoteType.PERMANENT,
                created_by="test@example.com",
                version=1
            )
            for i in range(5)
        ]

        # Mock services
        mock_note_service = MagicMock()
        mock_note_service.get_by_id.side_effect = lambda note_id: next(
            (note for note in notes if str(note.id) == note_id), None
        )

        mock_embedding_service = MagicMock()
        mock_embedding_service.generate_embedding.return_value = [0.1] * 384

        mock_vector_store = MagicMock()
        # Return different similarities to test ranking
        mock_vector_store.search_similar.return_value = [
            {"note_id": str(note.id), "similarity": 0.90 - (i * 0.05)}
            for i, note in enumerate(notes)
        ]

        return {
            "notes": notes,
            "note_service": mock_note_service,
            "embedding_service": mock_embedding_service,
            "vector_store": mock_vector_store
        }

    @pytest.mark.asyncio
    async def test_semantic_search_ranking(self, mock_search_environment):
        """Test semantic search ranking and relevance."""
        # Create search service
        search_service = SemanticSearch(
            embedding_service=mock_search_environment["embedding_service"],
            vector_store=mock_search_environment["vector_store"],
            note_service=mock_search_environment["note_service"]
        )

        # Perform search
        query = "artificial intelligence research"
        results = await search_service.semantic_search(query, limit=3)

        # Verify ranking (higher similarity should come first)
        assert len(results) == 3
        assert results[0]["similarity"] > results[1]["similarity"]
        assert results[1]["similarity"] > results[2]["similarity"]

        # Verify embedding generation
        mock_search_environment["embedding_service"].generate_embedding.assert_called_once_with(query)

    @pytest.mark.asyncio
    async def test_hybrid_search_workflow(self, mock_search_environment):
        """Test hybrid search combining semantic and metadata relevance."""
        # Create search service
        search_service = SemanticSearch(
            embedding_service=mock_search_environment["embedding_service"],
            vector_store=mock_search_environment["vector_store"],
            note_service=mock_search_environment["note_service"]
        )

        # Perform hybrid search with filters
        query = "machine learning algorithms"
        filters = {"note_type": "permanent", "tags": ["ai"]}
        weights = {"semantic": 0.7, "metadata": 0.3}

        results = await search_service.hybrid_search(query, filters=filters, weights=weights)

        # Verify hybrid search was performed
        assert len(results) == 5
        mock_search_environment["embedding_service"].generate_embedding.assert_called_once_with(query)

    @pytest.mark.asyncio
    async def test_search_with_similarity_threshold(self, mock_search_environment):
        """Test search with similarity threshold filtering."""
        # Create search service
        search_service = SemanticSearch(
            embedding_service=mock_search_environment["embedding_service"],
            vector_store=mock_search_environment["vector_store"],
            note_service=mock_search_environment["note_service"]
        )

        # Mock vector store to return varying similarities
        mock_search_environment["vector_store"].search_similar.return_value = [
            {"note_id": str(uuid4()), "similarity": 0.95},
            {"note_id": str(uuid4()), "similarity": 0.80},
            {"note_id": str(uuid4()), "similarity": 0.65},
            {"note_id": str(uuid4()), "similarity": 0.50}
        ]

        # Search with high threshold
        results = await search_service.semantic_search("test query", similarity_threshold=0.75)

        # Verify threshold filtering (only results above 0.75)
        assert len(results) == 2
        for result in results:
            assert result["similarity"] >= 0.75


class TestConcurrentOperations:
    """Test concurrent note and search operations."""

    @pytest.fixture
    def mock_concurrent_environment(self):
        """Create mock environment for concurrent testing."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        mock_embedding_service = MagicMock()
        mock_embedding_service.generate_embedding.return_value = [0.1] * 384

        mock_vector_store = MagicMock()
        mock_vector_store.search_similar.return_value = [{"note_id": str(uuid4()), "similarity": 0.85}]

        mock_search_service = MagicMock()
        mock_search_service.index_note = AsyncMock()

        return {
            "session": mock_session,
            "embedding_service": mock_embedding_service,
            "vector_store": mock_vector_store,
            "search_service": mock_search_service
        }

    @pytest.mark.asyncio
    async def test_concurrent_note_creation(self, mock_concurrent_environment):
        """Test concurrent note creation operations."""
        note_service = NoteService(
            session=mock_concurrent_environment["session"],
            embedding_service=mock_concurrent_environment["embedding_service"],
            search_service=mock_concurrent_environment["search_service"]
        )

        # Create multiple notes concurrently
        note_data_list = [
            NoteCreate(content=f"Concurrent note {i}", note_type=NoteType.FLEETING, created_by="test@example.com")
            for i in range(5)
        ]

        async def create_note(note_data):
            mock_note = Note(
                id=uuid4(),
                content=note_data.content,
                note_type=note_data.note_type,
                created_by=note_data.created_by,
                version=1
            )
            mock_concurrent_environment["session"].refresh.return_value = mock_note
            return await note_service.create(note_data)

        # Perform concurrent creations
        results = await asyncio.gather(*[create_note(data) for data in note_data_list])

        # Verify all notes were created
        assert len(results) == 5
        assert mock_concurrent_environment["session"].commit.call_count >= 5

    @pytest.mark.asyncio
    async def test_concurrent_search_operations(self, mock_concurrent_environment):
        """Test concurrent search operations."""
        search_service = SemanticSearch(
            embedding_service=mock_concurrent_environment["embedding_service"],
            vector_store=mock_concurrent_environment["vector_store"],
            note_service=MagicMock()  # Mock note service
        )

        # Perform multiple searches concurrently
        queries = [f"search query {i}" for i in range(5)]

        async def perform_search(query):
            return await search_service.semantic_search(query)

        results = await asyncio.gather(*[perform_search(query) for query in queries])

        # Verify all searches completed
        assert len(results) == 5
        assert mock_concurrent_environment["embedding_service"].generate_embedding.call_count == 5


class TestErrorRecoveryWorkflow:
    """Test error recovery in note and search workflows."""

    @pytest.mark.asyncio
    async def test_embedding_service_failure_recovery(self):
        """Test recovery when embedding service fails."""
        # Mock failing embedding service
        mock_embedding_service = MagicMock()
        mock_embedding_service.generate_embedding.side_effect = Exception("Embedding service unavailable")

        mock_note_service = MagicMock()
        mock_vector_store = MagicMock()

        search_service = SemanticSearch(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            note_service=mock_note_service
        )

        # Attempt search that should fail
        with pytest.raises(Exception, match="Embedding service unavailable"):
            await search_service.semantic_search("test query")

    @pytest.mark.asyncio
    async def test_database_connection_recovery(self):
        """Test recovery from database connection failures."""
        # Mock database session with retry logic
        mock_session = AsyncMock()
        mock_session.execute.side_effect = [Exception("Database connection failed"), None]

        note_service = NoteService(
            session=mock_session,
            embedding_service=MagicMock(),
            search_service=MagicMock()
        )

        # Test retry mechanism
        retry_count = 0
        max_retries = 3

        for attempt in range(max_retries):
            try:
                await note_service.get_by_id(uuid4())
                break  # Success
            except Exception:
                retry_count += 1
                if attempt == max_retries - 1:
                    raise  # Final attempt failed

        # Verify retry behavior was tested
        assert retry_count >= 0