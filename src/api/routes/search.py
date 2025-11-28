"""Search API routes for BrainForge."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/search")
async def search_notes():
    """Search notes with semantic and hybrid search."""
    return {"message": "Search endpoint - to be implemented"}
