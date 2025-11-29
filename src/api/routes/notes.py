"""Notes API routes for BrainForge."""

import logging
import asyncio
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import DatabaseSession, NoteServiceDep, EmbeddingServiceDep
from ...models.note import Note, NoteCreate, NoteUpdate, NoteType
from ...services.embedding_generator import EmbeddingGenerator
from ...services.vector_store import VectorStore
from ...services.database import NoteService, EmbeddingService

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_database_service(note_service: NoteService, embedding_service: EmbeddingService) -> Any:
    """Get a database service instance for embedding operations."""
    # Create a simple database service wrapper that uses the existing services
    class EmbeddingDatabaseService:
        def __init__(self, note_service: NoteService, embedding_service: EmbeddingService):
            self.note_service = note_service
            self.embedding_service = embedding_service
            
        async def get_embedding_by_note_id(self, session: AsyncSession, note_id: UUID) -> Any:
            """Get embedding by note ID."""
            return await self.embedding_service.get_by_note(session, note_id)
            
        async def get_note_by_id(self, session: AsyncSession, note_id: UUID) -> Any:
            """Get note by ID."""
            return await self.note_service.get(session, note_id)
            
        async def list_notes(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[Any]:
            """List notes with pagination."""
            return await self.note_service.list(session, skip, limit)
    
    return EmbeddingDatabaseService(note_service, embedding_service)


async def generate_embedding_for_note(
    note_id: UUID, 
    note_content: str,
    session: AsyncSession,
    note_service: NoteService,
    embedding_service: EmbeddingService
):
    """Generate and store embedding for a note."""
    try:
        # Create database service wrapper
        database_service = await get_database_service(note_service, embedding_service)
        
        # Initialize services
        embedding_generator = EmbeddingGenerator(database_service)
        vector_store = VectorStore(database_service)
        
        # Generate embedding for the note content
        embedding_vector = await embedding_generator.generate_embedding(note_content)
        
        if embedding_vector:
            # Store the embedding in the vector store
            await vector_store.store_vector(
                note_id=str(note_id),
                vector=embedding_vector,
                model_name=embedding_generator.model_name,
                model_version=embedding_generator.model_version
            )
            logger.info(f"Successfully generated and stored embedding for note {note_id}")
        else:
            logger.warning(f"Failed to generate embedding for note {note_id}")
            
    except Exception as e:
        logger.error(f"Error generating embedding for note {note_id}: {e}")


@router.get("/notes", response_model=list[Note])
async def list_notes(
    skip: int = 0, 
    limit: int = 100,
    session: AsyncSession = DatabaseSession,
    note_service: NoteService = NoteServiceDep
):
    """List notes with filtering and search."""
    try:
        notes = await note_service.list(session, skip=skip, limit=limit)
        return notes
    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notes"
        )


@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    session: AsyncSession = DatabaseSession,
    note_service: NoteService = NoteServiceDep,
    embedding_service: EmbeddingService = EmbeddingServiceDep
):
    """Create a new note and generate its embedding."""
    try:
        # Validate the note data using Pydantic model
        validated_data = note_data.model_dump()
        
        # Create the note
        note = await note_service.create(session, validated_data)
        
        # Generate embedding asynchronously (fire and forget)
        asyncio.create_task(
            generate_embedding_for_note(
                note_id=note.id,
                note_content=note.content,
                session=session,
                note_service=note_service,
                embedding_service=embedding_service
            )
        )
        
        return note
    except ValueError as e:
        logger.warning(f"Validation error creating note: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid note data: {e}"
        )
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create note"
        )


@router.get("/notes/{note_id}", response_model=Note)
async def get_note(
    note_id: UUID,
    session: AsyncSession = DatabaseSession,
    note_service: NoteService = NoteServiceDep
):
    """Get a specific note."""
    try:
        note = await note_service.get(session, note_id)
        if note is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        return note
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve note"
        )


@router.put("/notes/{note_id}", response_model=Note)
async def update_note(
    note_id: UUID, 
    note_data: NoteUpdate,
    session: AsyncSession = DatabaseSession,
    note_service: NoteService = NoteServiceDep,
    embedding_service: EmbeddingService = EmbeddingServiceDep
):
    """Update a note and regenerate its embedding if content changed."""
    try:
        # Validate the update data using Pydantic model
        validated_data = note_data.model_dump()
        
        # Get the current note to check if content changed
        current_note = await note_service.get(session, note_id)
        if current_note is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        # Update the note
        note = await note_service.update(session, note_id, validated_data)
        
        # Check if content changed and regenerate embedding if needed
        if note and hasattr(note, 'content') and note.content != current_note.content:
            asyncio.create_task(
                generate_embedding_for_note(
                    note_id=note_id,
                    note_content=note.content,
                    session=session,
                    note_service=note_service,
                    embedding_service=embedding_service
                )
            )
            logger.info(f"Content changed for note {note_id}, regenerating embedding")
        
        return note
    except ValueError as e:
        logger.warning(f"Validation error updating note: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid note data: {e}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update note"
        )


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    session: AsyncSession = DatabaseSession,
    note_service: NoteService = NoteServiceDep,
    embedding_service: EmbeddingService = EmbeddingServiceDep
):
    """Delete a note and its associated embedding."""
    try:
        # Delete the note
        success = await note_service.delete(session, note_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        # Delete associated embeddings (fire and forget)
        asyncio.create_task(
            delete_embeddings_for_note(note_id, session, embedding_service)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete note"
        )


async def delete_embeddings_for_note(
    note_id: UUID,
    session: AsyncSession,
    embedding_service: EmbeddingService
):
    """Delete all embeddings associated with a note."""
    try:
        # Get embeddings for the note
        embeddings = await embedding_service.get_by_note(session, note_id)
        
        # Delete each embedding
        for embedding in embeddings:
            await embedding_service.delete(session, embedding.id)
            
        logger.info(f"Deleted {len(embeddings)} embeddings for note {note_id}")
        
    except Exception as e:
        logger.error(f"Error deleting embeddings for note {note_id}: {e}")