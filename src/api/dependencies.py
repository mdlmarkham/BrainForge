"""FastAPI dependencies for BrainForge."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import db_config


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency for FastAPI routes."""
    async for session in db_config.get_session():
        yield session


# Service dependencies
def get_note_service() -> "NoteService":
    """Get note service dependency."""
    from ..services.database import NoteService
    return NoteService()


def get_link_service() -> "LinkService":
    """Get link service dependency."""
    from ..services.database import LinkService
    return LinkService()


def get_embedding_service() -> "EmbeddingService":
    """Get embedding service dependency."""
    from ..services.database import EmbeddingService
    return EmbeddingService()


def get_agent_run_service() -> "AgentRunService":
    """Get agent run service dependency."""
    from ..services.database import AgentRunService
    return AgentRunService()


def get_version_history_service() -> "VersionHistoryService":
    """Get version history service dependency."""
    from ..services.database import VersionHistoryService
    return VersionHistoryService()


# Type aliases for dependency injection
DatabaseSession = Depends(get_db)
NoteServiceDep = Depends(get_note_service)
LinkServiceDep = Depends(get_link_service)
EmbeddingServiceDep = Depends(get_embedding_service)
AgentRunServiceDep = Depends(get_agent_run_service)
VersionHistoryServiceDep = Depends(get_version_history_service)