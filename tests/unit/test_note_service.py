"""Unit tests for note service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.note import Note, NoteCreate, NoteType
from src.services.database import NoteService


class TestNoteService:
    """Test note service functionality."""

    @pytest.fixture
    def note_service(self):
        """Create a note service instance."""
        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()
        mock_search_service = MagicMock()
        
        return NoteService(
            session=mock_session,
            embedding_service=mock_embedding_service,
            search_service=mock_search_service
        )

    @pytest.fixture
    def test_note_data(self):
        """Create test note data."""
        return NoteCreate(
            content="Test note content about artificial intelligence",
            note_type=NoteType.FLEETING,
            created_by="test@example.com"
        )

    @pytest.mark.asyncio
    async def test_create_note_success(self, note_service, test_note_data):
        """Test successful note creation."""
        # Mock database operations
        mock_note = Note(
            id=uuid4(),
            content=test_note_data.content,
            note_type=test_note_data.note_type,
            created_by=test_note_data.created_by,
            version=1
        )
        
        note_service.session.add = MagicMock()
        note_service.session.commit = AsyncMock()
        note_service.session.refresh = AsyncMock(return_value=mock_note)
        
        # Mock embedding generation
        note_service.embedding_service.generate_embedding.return_value = [0.1] * 384
        
        # Mock search indexing
        note_service.search_service.index_note = AsyncMock()

        # Create note
        result = await note_service.create(test_note_data)

        # Verify note creation
        assert result.content == test_note_data.content
        assert result.note_type == test_note_data.note_type
        note_service.session.add.assert_called_once()
        note_service.session.commit.assert_called_once()
        note_service.embedding_service.generate_embedding.assert_called_once_with(test_note_data.content)
        note_service.search_service.index_note.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_note_validation_error(self, note_service):
        """Test note creation with validation errors."""
        # Test empty content
        invalid_data = NoteCreate(
            content="",  # Empty content should fail
            note_type=NoteType.FLEETING,
            created_by="test@example.com"
        )
        
        with pytest.raises(ValueError, match="Note content cannot be empty"):
            await note_service.create(invalid_data)

    @pytest.mark.asyncio
    async def test_get_note_by_id(self, note_service):
        """Test retrieving a note by ID."""
        note_id = uuid4()
        mock_note = Note(
            id=note_id,
            content="Test content",
            note_type=NoteType.PERMANENT,
            created_by="test@example.com",
            version=1
        )
        
        # Mock database query
        note_service.session.execute.return_value.scalar_one_or_none.return_value = mock_note

        # Get note
        result = await note_service.get_by_id(note_id)

        # Verify note retrieval
        assert result.id == note_id
        assert result.content == "Test content"
        note_service.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_note_not_found(self, note_service):
        """Test retrieving a non-existent note."""
        note_id = uuid4()
        
        # Mock no result found
        note_service.session.execute.return_value.scalar_one_or_none.return_value = None

        # Get non-existent note
        result = await note_service.get_by_id(note_id)

        # Verify None is returned
        assert result is None

    @pytest.mark.asyncio
    async def test_update_note_success(self, note_service):
        """Test successful note update."""
        note_id = uuid4()
        original_note = Note(
            id=note_id,
            content="Original content",
            note_type=NoteType.PERMANENT,
            created_by="test@example.com",
            version=1
        )
        
        update_data = {
            "content": "Updated content",
            "version": 2
        }

        # Mock existing note
        note_service.session.execute.return_value.scalar_one_or_none.return_value = original_note
        note_service.session.commit = AsyncMock()
        note_service.session.refresh = AsyncMock()

        # Mock embedding regeneration
        note_service.embedding_service.generate_embedding.return_value = [0.1] * 384
        note_service.search_service.update_note_index = AsyncMock()

        # Update note
        result = await note_service.update(note_id, update_data)

        # Verify update operations
        note_service.session.commit.assert_called_once()
        note_service.embedding_service.generate_embedding.assert_called_once_with("Updated content")
        note_service.search_service.update_note_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_note_not_found(self, note_service):
        """Test updating a non-existent note."""
        note_id = uuid4()
        update_data = {"content": "Updated content", "version": 2}
        
        # Mock no note found
        note_service.session.execute.return_value.scalar_one_or_none.return_value = None

        # Update non-existent note
        result = await note_service.update(note_id, update_data)

        # Verify None is returned
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_note_success(self, note_service):
        """Test successful note deletion."""
        note_id = uuid4()
        mock_note = Note(
            id=note_id,
            content="Test content",
            note_type=NoteType.PERMANENT,
            created_by="test@example.com",
            version=1
        )
        
        # Mock existing note
        note_service.session.execute.return_value.scalar_one_or_none.return_value = mock_note
        note_service.session.delete = MagicMock()
        note_service.session.commit = AsyncMock()
        note_service.search_service.remove_note_from_index = AsyncMock()

        # Delete note
        result = await note_service.delete(note_id)

        # Verify deletion operations
        assert result is True
        note_service.session.delete.assert_called_once_with(mock_note)
        note_service.session.commit.assert_called_once()
        note_service.search_service.remove_note_from_index.assert_called_once_with(note_id)

    @pytest.mark.asyncio
    async def test_delete_note_not_found(self, note_service):
        """Test deleting a non-existent note."""
        note_id = uuid4()
        
        # Mock no note found
        note_service.session.execute.return_value.scalar_one_or_none.return_value = None

        # Delete non-existent note
        result = await note_service.delete(note_id)

        # Verify False is returned
        assert result is False

    @pytest.mark.asyncio
    async def test_list_notes(self, note_service):
        """Test listing notes with pagination."""
        # Mock multiple notes
        mock_notes = [
            Note(id=uuid4(), content=f"Note {i}", note_type=NoteType.FLEETING, created_by="test@example.com", version=1)
            for i in range(5)
        ]
        
        note_service.session.execute.return_value.scalars.return_value.all.return_value = mock_notes
        note_service.session.execute.return_value.scalar.return_value = len(mock_notes)

        # List notes
        result = await note_service.list(skip=0, limit=10)

        # Verify listing
        assert len(result["notes"]) == 5
        assert result["total"] == 5
        note_service.session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_list_notes_with_filters(self, note_service):
        """Test listing notes with filters."""
        mock_notes = [
            Note(id=uuid4(), content="AI note", note_type=NoteType.PERMANENT, created_by="test@example.com", version=1)
        ]
        
        note_service.session.execute.return_value.scalars.return_value.all.return_value = mock_notes
        note_service.session.execute.return_value.scalar.return_value = len(mock_notes)

        # List notes with filters
        filters = {"note_type": "permanent", "tags": ["ai"]}
        result = await note_service.list(skip=0, limit=10, filters=filters)

        # Verify filtered listing
        assert len(result["notes"]) == 1
        assert result["notes"][0].note_type == NoteType.PERMANENT

    @pytest.mark.asyncio
    async def test_create_note_with_ai_generated_content(self, note_service):
        """Test creating AI-generated note with justification."""
        ai_note_data = NoteCreate(
            content="AI-generated content about machine learning",
            note_type=NoteType.AGENT_GENERATED,
            created_by="ai@example.com",
            is_ai_generated=True,
            ai_justification="Generated by research agent v1.0"
        )
        
        # Mock successful creation
        mock_note = Note(
            id=uuid4(),
            content=ai_note_data.content,
            note_type=ai_note_data.note_type,
            created_by=ai_note_data.created_by,
            is_ai_generated=True,
            ai_justification=ai_note_data.ai_justification,
            version=1
        )
        
        note_service.session.add = MagicMock()
        note_service.session.commit = AsyncMock()
        note_service.session.refresh = AsyncMock(return_value=mock_note)
        note_service.embedding_service.generate_embedding.return_value = [0.1] * 384
        note_service.search_service.index_note = AsyncMock()

        # Create AI-generated note
        result = await note_service.create(ai_note_data)

        # Verify AI note creation
        assert result.is_ai_generated is True
        assert result.ai_justification == "Generated by research agent v1.0"

    @pytest.mark.asyncio
    async def test_create_ai_note_missing_justification(self, note_service):
        """Test creating AI-generated note without justification."""
        invalid_ai_note = NoteCreate(
            content="AI-generated content",
            note_type=NoteType.AGENT_GENERATED,
            created_by="ai@example.com",
            is_ai_generated=True,
            ai_justification=None  # Missing justification
        )
        
        with pytest.raises(ValueError, match="AI-generated notes require justification"):
            await note_service.create(invalid_ai_note)


class TestNoteValidation:
    """Test note validation logic."""

    @pytest.fixture
    def note_service(self):
        """Create a note service instance."""
        return NoteService(session=AsyncMock(), embedding_service=MagicMock(), search_service=MagicMock())

    def test_validate_note_content(self, note_service):
        """Test note content validation."""
        # Valid content
        assert note_service._validate_note_content("Valid note content") is True
        
        # Empty content
        with pytest.raises(ValueError, match="Note content cannot be empty"):
            note_service._validate_note_content("")
        
        # Whitespace-only content
        with pytest.raises(ValueError, match="Note content cannot be empty"):
            note_service._validate_note_content("   ")

    def test_validate_note_type(self, note_service):
        """Test note type validation."""
        # Valid note types
        for note_type in NoteType:
            assert note_service._validate_note_type(note_type) is True
        
        # Invalid note type
        with pytest.raises(ValueError, match="Invalid note type"):
            note_service._validate_note_type("invalid_type")

    def test_validate_ai_generated_note(self, note_service):
        """Test AI-generated note validation."""
        # Valid AI note with justification
        assert note_service._validate_ai_generated_note(True, "Valid justification") is True
        
        # AI note without justification
        with pytest.raises(ValueError, match="AI-generated notes require justification"):
            note_service._validate_ai_generated_note(True, None)
        
        # Non-AI note (should not require justification)
        assert note_service._validate_ai_generated_note(False, None) is True


class TestNotePerformance:
    """Test note service performance characteristics."""

    @pytest.fixture
    def note_service(self):
        """Create a note service instance."""
        mock_session = AsyncMock()
        mock_embedding_service = MagicMock()
        mock_search_service = MagicMock()
        
        return NoteService(
            session=mock_session,
            embedding_service=mock_embedding_service,
            search_service=mock_search_service
        )

    @pytest.mark.asyncio
    async def test_note_creation_performance(self, note_service):
        """Test note creation performance."""
        import time
        
        note_data = NoteCreate(
            content="Performance test note content",
            note_type=NoteType.FLEETING,
            created_by="test@example.com"
        )
        
        # Mock fast operations
        note_service.session.add = MagicMock()
        note_service.session.commit = AsyncMock()
        note_service.session.refresh = AsyncMock(return_value=MagicMock())
        note_service.embedding_service.generate_embedding.return_value = [0.1] * 384
        note_service.search_service.index_note = AsyncMock()

        start_time = time.time()
        result = await note_service.create(note_data)
        end_time = time.time()

        creation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Verify reasonable performance
        assert creation_time < 1000  # Should complete within 1 second
        assert result is not None

    @pytest.mark.asyncio
    async def test_batch_note_operations(self, note_service):
        """Test performance of batch note operations."""
        import asyncio
        
        # Mock multiple note creations
        note_data_list = [
            NoteCreate(content=f"Note {i}", note_type=NoteType.FLEETING, created_by="test@example.com")
            for i in range(10)
        ]
        
        async def create_note(note_data):
            return await note_service.create(note_data)

        # Perform batch creations
        start_time = time.time()
        results = await asyncio.gather(*[create_note(data) for data in note_data_list])
        end_time = time.time()

        batch_time = (end_time - start_time) * 1000
        
        # Verify batch performance
        assert len(results) == 10
        assert batch_time < 5000  # Should complete within 5 seconds for 10 notes