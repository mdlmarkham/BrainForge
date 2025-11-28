"""Ingestion API routes for BrainForge."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/ingestion")
async def ingest_content():
    """Ingest external content."""
    return {"message": "Ingestion endpoint - to be implemented"}
