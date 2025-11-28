"""Vault API routes for BrainForge."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/vault/sync")
async def sync_vault():
    """Sync with Obsidian vault."""
    return {"message": "Vault sync endpoint - to be implemented"}
