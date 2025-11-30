"""Vault API routes for BrainForge."""

from fastapi import APIRouter

from src.models.orm.user import User

from ..dependencies import CurrentUser

router = APIRouter()


@router.post("/vault/sync")
async def sync_vault(
    current_user: User = CurrentUser
):
    """Sync with Obsidian vault."""
    return {"message": "Vault sync endpoint - to be implemented"}
