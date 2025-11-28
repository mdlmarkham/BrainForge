"""Notes API routes for BrainForge."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.models.note import Note, NoteCreate, NoteUpdate, NoteType
from src.services.database import NoteService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service (in production, this would be dependency injected)
note_service = NoteService("postgresql://user:password@localhost/brainforge")


@router.get("/notes", response_model=list[Note])
async def list_notes(skip: int = 0, limit: int = 100):
    """List notes with filtering and search."""
    try:
        notes = await note_service.list(skip=skip, limit=limit)
        return notes
    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notes"
        )


@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_note(note_data: NoteCreate):
    """Create a new note."""
    try:
        # Validate the note data using Pydantic model
        validated_data = note_data.model_dump()
        
        # Create the note
        note = await note_service.create(NoteCreate(**validated_data))
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
async def get_note(note_id: UUID):
    """Get a specific note."""
    try:
        note = await note_service.get(note_id)
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
async def update_note(note_id: UUID, note_data: NoteUpdate):
    """Update a note."""
    try:
        # Validate the update data using Pydantic model
        validated_data = note_data.model_dump()
        
        # Update the note
        note = await note_service.update(note_id, NoteUpdate(**validated_data))
        if note is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
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
async def delete_note(note_id: UUID):
    """Delete a note."""
    try:
        success = await note_service.delete(note_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete note"
        )
