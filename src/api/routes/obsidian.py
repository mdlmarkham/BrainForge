"""Obsidian API routes for BrainForge integration with Obsidian Local REST API."""

from typing import List, Optional
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.services.obsidian import ObsidianService, ObsidianNote, ObsidianServerInfo, ObsidianCommand
from src.config.database import db_config
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/obsidian", tags=["obsidian"])


class NoteRequest(BaseModel):
    """Request model for note operations."""
    filename: str
    content: Optional[str] = None
    as_json: bool = False


class NoteResponse(BaseModel):
    """Response model for note operations."""
    success: bool
    note: Optional[ObsidianNote] = None
    message: Optional[str] = None


class ServerInfoResponse(BaseModel):
    """Response model for server info."""
    success: bool
    info: Optional[ObsidianServerInfo] = None
    message: Optional[str] = None


class VaultFilesResponse(BaseModel):
    """Response model for vault files listing."""
    success: bool
    files: List[str] = []
    message: Optional[str] = None


class CommandsResponse(BaseModel):
    """Response model for available commands."""
    success: bool
    commands: List[ObsidianCommand] = []
    message: Optional[str] = None


class PeriodicNoteRequest(BaseModel):
    """Request model for periodic note operations."""
    period: str
    content: str
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None


async def get_obsidian_service() -> ObsidianService:
    """Dependency to get Obsidian service instance."""
    base_url = os.getenv("OBSIDIAN_API_URL", "http://localhost:27124")
    token = os.getenv("OBSIDIAN_API_TOKEN")
    return ObsidianService(base_url=base_url, token=token)


@router.get("/server", response_model=ServerInfoResponse)
async def get_obsidian_server_info(
    obsidian_service: ObsidianService = Depends(get_obsidian_service)
) -> ServerInfoResponse:
    """
    Get Obsidian server information and authentication status.
    
    Returns:
        ServerInfoResponse: Server information including version and authentication status
    """
    try:
        info = await obsidian_service.get_server_info()
        return ServerInfoResponse(success=True, info=info)
    except Exception as e:
        return ServerInfoResponse(success=False, message=str(e))


@router.get("/notes/{filename:path}", response_model=NoteResponse)
async def get_obsidian_note(
    filename: str,
    as_json: bool = False,
    obsidian_service: ObsidianService = Depends(get_obsidian_service)
) -> NoteResponse:
    """
    Get a note from Obsidian vault.
    
    Args:
        filename: Path to the note relative to vault root
        as_json: Whether to return JSON representation with metadata
        
    Returns:
        NoteResponse: The note content and metadata
    """
    try:
        note = await obsidian_service.get_note(filename, as_json=as_json)
        return NoteResponse(success=True, note=note)
    except Exception as e:
        return NoteResponse(success=False, message=str(e))


@router.post("/notes/{filename:path}", response_model=NoteResponse)
async def create_or_append_note(
    filename: str,
    request: NoteRequest,
    obsidian_service: ObsidianService = Depends(get_obsidian_service)
) -> NoteResponse:
    """
    Create or append to a note in Obsidian vault.
    
    Args:
        filename: Path to the note relative to vault root
        request: Note request containing content to append
        
    Returns:
        NoteResponse: Success status and optional message
    """
    try:
        if request.content:
            await obsidian_service.create_or_append_note(filename, request.content)
            return NoteResponse(success=True, message="Note created/updated successfully")
        else:
            return NoteResponse(success=False, message="Content is required")
    except Exception as e:
        return NoteResponse(success=False, message=str(e))


@router.get("/active", response_model=NoteResponse)
async def get_active_note(
    as_json: bool = False,
    obsidian_service: ObsidianService = Depends(get_obsidian_service)
) -> NoteResponse:
    """
    Get the currently active note in Obsidian.
    
    Args:
        as_json: Whether to return JSON representation with metadata
        
    Returns:
        NoteResponse: The active note, or empty response if no active note
    """
    try:
        note = await obsidian_service.get_active_note(as_json=as_json)
        if note:
            return NoteResponse(success=True, note=note)
        else:
            return NoteResponse(success=True, message="No active note")
    except Exception as e:
        return NoteResponse(success=False, message=str(e))


@router.post("/active", response_model=NoteResponse)
async def append_to_active_note(
    request: NoteRequest,
    obsidian_service: ObsidianService = Depends(get_obsidian_service)
) -> NoteResponse:
    """
    Append content to the currently active note.
    
    Args:
        request: Note request containing content to append
        
    Returns:
        NoteResponse: Success status and optional message
    """
    try:
        if request.content:
            await obsidian_service.append_to_active_note(request.content)
            return NoteResponse(success=True, message="Content appended to active note")
        else:
            return NoteResponse(success=False, message="Content is required")
    except Exception as e:
        return NoteResponse(success=False, message=str(e))


@router.get("/vault", response_model=VaultFilesResponse)
async def list_vault_files(
    directory: str = '',
    obsidian_service: ObsidianService = Depends(get_obsidian_service)
) -> VaultFilesResponse:
    """
    List files in a directory of the Obsidian vault.
    
    Args:
        directory: Directory path relative to vault root (empty for root)
        
    Returns:
        VaultFilesResponse: List of file paths in the directory
    """
    try:
        files = await obsidian_service.list_vault_files(directory)
        return VaultFilesResponse(success=True, files=files)
    except Exception as e:
        return VaultFilesResponse(success=False, message=str(e))


@router.get("/commands", response_model=CommandsResponse)
async def get_available_commands(
    obsidian_service: ObsidianService = Depends(get_obsidian_service)
) -> CommandsResponse:
    """
    Get available Obsidian commands.
    
    Returns:
        CommandsResponse: List of available commands
    """
    try:
        commands = await obsidian_service.get_available_commands()
        return CommandsResponse(success=True, commands=commands)
    except Exception as e:
        return CommandsResponse(success=False, message=str(e))


@router.post("/periodic", response_model=NoteResponse)
async def create_periodic_note(
    request: PeriodicNoteRequest,
    obsidian_service: ObsidianService = Depends(get_obsidian_service)
) -> NoteResponse:
    """
    Create or append to a periodic note.
    
    Args:
        request: Periodic note request containing period, content, and optional date
        
    Returns:
        NoteResponse: Success status and optional message
    """
    try:
        await obsidian_service.create_periodic_note(
            request.period,
            request.content,
            request.year,
            request.month,
            request.day
        )
        return NoteResponse(success=True, message="Periodic note created/updated successfully")
    except Exception as e:
        return NoteResponse(success=False, message=str(e))


@router.post("/sync")
async def sync_with_obsidian(
    db: AsyncSession = Depends(db_config.get_session),
    obsidian_service: ObsidianService = Depends(get_obsidian_service)
):
    """
    Sync BrainForge database with Obsidian vault.
    
    This endpoint will:
    1. List all files in the Obsidian vault
    2. Compare with existing notes in BrainForge database
    3. Create/update notes in BrainForge as needed
    4. Handle conflicts and versioning
    
    Returns:
        Sync status and statistics
    """
    # TODO: Implement comprehensive sync logic
    try:
        # Get vault files
        files = await obsidian_service.list_vault_files()
        
        # For now, return basic sync information
        return {
            "success": True,
            "message": f"Found {len(files)} files in vault",
            "files_count": len(files),
            "sync_implemented": False  # Mark as not fully implemented yet
        }
    except Exception as e:
        return {"success": False, "message": str(e)}