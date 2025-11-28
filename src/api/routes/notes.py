"""Notes API routes for BrainForge."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/notes")
async def list_notes():
    """List notes with filtering and search."""
    return {"message": "Notes endpoint - to be implemented"}


@router.post("/notes")
async def create_note():
    """Create a new note."""
    return {"message": "Create note endpoint - to be implemented"}


@router.get("/notes/{note_id}")
async def get_note(note_id: str):
    """Get a specific note."""
    return {"message": f"Get note {note_id} endpoint - to be implemented"}


@router.put("/notes/{note_id}")
async def update_note(note_id: str):
    """Update a note."""
    return {"message": f"Update note {note_id} endpoint - to be implemented"}


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    """Delete a note."""
    return {"message": f"Delete note {note_id} endpoint - to be implemented"}
