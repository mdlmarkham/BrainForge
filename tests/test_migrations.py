"""Integration tests for BrainForge database migrations."""

import os
import pytest
import asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import db_config
from src.models.orm.note import Note
from src.models.orm.link import Link
from src.models.orm.embedding import Embedding
from src.models.orm.agent_run import AgentRun, AgentRunStatus
from src.models.orm.version_history import VersionHistory


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_session():
    """Create a test database session."""
    # Use test database URL if available
    test_url = os.getenv("TEST_DATABASE_URL")
    if not test_url:
        pytest.skip("TEST_DATABASE_URL environment variable not set")
    
    # Create tables
    await db_config.create_tables()
    
    # Get a session
    async for session in db_config.get_session():
        yield session
    
    # Clean up
    await db_config.drop_tables()


@pytest.mark.asyncio
async def test_migration_creates_tables(test_session: AsyncSession):
    """Test that migration creates all required tables."""
    # Check that tables exist by trying to insert data
    note_data = {
        "content": "Test note content",
        "note_type": "fleeting",
        "created_by": "test_user",
        "metadata": {"test": "data"}
    }
    
    note = Note(**note_data)
    test_session.add(note)
    await test_session.commit()
    await test_session.refresh(note)
    
    assert note.id is not None
    assert note.content == "Test note content"
    assert note.note_type == "fleeting"


@pytest.mark.asyncio
async def test_note_crud_operations(test_session: AsyncSession):
    """Test basic CRUD operations for notes."""
    from src.services.database import NoteService
    
    note_service = NoteService()
    
    # Create
    note_data = {
        "content": "Test note for CRUD operations",
        "note_type": "permanent",
        "created_by": "test_user",
        "metadata": {"category": "test"}
    }
    
    note = await note_service.create(test_session, note_data)
    assert note.id is not None
    
    # Read
    retrieved_note = await note_service.get(test_session, note.id)
    assert retrieved_note is not None
    assert retrieved_note.content == "Test note for CRUD operations"
    
    # Update
    update_data = {"content": "Updated note content"}
    updated_note = await note_service.update(test_session, note.id, update_data)
    assert updated_note.content == "Updated note content"
    
    # Delete
    delete_result = await note_service.delete(test_session, note.id)
    assert delete_result is True
    
    # Verify deletion
    deleted_note = await note_service.get(test_session, note.id)
    assert deleted_note is None


@pytest.mark.asyncio
async def test_link_creation(test_session: AsyncSession):
    """Test link creation between notes."""
    from src.services.database import NoteService, LinkService
    
    note_service = NoteService()
    link_service = LinkService()
    
    # Create two notes
    note1_data = {
        "content": "Source note",
        "note_type": "fleeting",
        "created_by": "test_user"
    }
    note1 = await note_service.create(test_session, note1_data)
    
    note2_data = {
        "content": "Target note",
        "note_type": "fleeting",
        "created_by": "test_user"
    }
    note2 = await note_service.create(test_session, note2_data)
    
    # Create link
    link_data = {
        "source_note_id": note1.id,
        "target_note_id": note2.id,
        "relation_type": "cites",
        "created_by": "test_user"
    }
    
    link = await link_service.create(test_session, link_data)
    assert link.id is not None
    assert link.source_note_id == note1.id
    assert link.target_note_id == note2.id


@pytest.mark.asyncio
async def test_agent_run_workflow(test_session: AsyncSession):
    """Test agent run creation and status workflow."""
    from src.services.database import AgentRunService
    
    agent_run_service = AgentRunService()
    
    agent_run_data = {
        "agent_name": "test_agent",
        "agent_version": "1.0.0",
        "input_parameters": {"prompt": "Test prompt"},
        "output_note_ids": [],
        "status": "pending_review"
    }
    
    agent_run = await agent_run_service.create(test_session, agent_run_data)
    assert agent_run.id is not None
    assert agent_run.status == "pending_review"
    
    # Update status
    update_data = {"status": "success", "review_status": "approved", "human_reviewer": "test_user"}
    updated_run = await agent_run_service.update(test_session, agent_run.id, update_data)
    assert updated_run.status == "success"
    assert updated_run.review_status == "approved"


@pytest.mark.asyncio
async def test_version_history_tracking(test_session: AsyncSession):
    """Test version history tracking for notes."""
    from src.services.database import NoteService, VersionHistoryService
    
    note_service = NoteService()
    version_service = VersionHistoryService()
    
    # Create initial note
    note_data = {
        "content": "Initial content",
        "note_type": "permanent",
        "created_by": "test_user"
    }
    note = await note_service.create(test_session, note_data)
    
    # Create version history entry
    version_data = {
        "note_id": note.id,
        "version": 1,
        "content": "Initial content",
        "created_by": "test_user",
        "change_reason": "Initial creation"
    }
    
    version = await version_service.create(test_session, version_data)
    assert version.id is not None
    assert version.note_id == note.id
    assert version.version == 1


@pytest.mark.asyncio
async def test_embedding_creation(test_session: AsyncSession):
    """Test embedding creation for notes."""
    from src.services.database import NoteService, EmbeddingService
    
    note_service = NoteService()
    embedding_service = EmbeddingService()
    
    # Create note
    note_data = {
        "content": "Note for embedding test",
        "note_type": "permanent",
        "created_by": "test_user"
    }
    note = await note_service.create(test_session, note_data)
    
    # Create embedding
    embedding_data = {
        "note_id": note.id,
        "vector": [0.1, 0.2, 0.3] * 512,  # 1536-dimensional vector
        "model_version": "text-embedding-3-small"
    }
    
    embedding = await embedding_service.create(test_session, embedding_data)
    assert embedding.id is not None
    assert embedding.note_id == note.id
    assert len(embedding.vector) == 1536