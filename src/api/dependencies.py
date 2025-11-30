"""FastAPI dependencies for BrainForge."""

import os
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.orm.user import User
from src.services.auth import AuthService

from ..config.database import db_config


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency for FastAPI routes."""
    async for session in db_config.get_session():
        yield session


# Service dependencies
def get_note_service():
    """Get note service dependency."""
    from ..services.database import NoteService
    return NoteService()


def get_link_service():
    """Get link service dependency."""
    from ..services.database import LinkService
    return LinkService()


def get_embedding_service():
    """Get embedding service dependency."""
    from ..services.database import EmbeddingService
    return EmbeddingService()


def get_agent_run_service():
    """Get agent run service dependency."""
    from ..services.database import AgentRunService
    return AgentRunService()


def get_version_history_service():
    """Get version history service dependency."""
    from ..services.database import VersionHistoryService
    return VersionHistoryService()


security = HTTPBearer()

# Get secret key from environment variable - required for security
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise ValueError("SECRET_KEY environment variable is required for authentication")

auth_service = AuthService(secret_key=secret_key)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    user_id = auth_service.verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(session, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user

# Type aliases for dependency injection
DatabaseSession = Depends(get_db)
NoteServiceDep = Depends(get_note_service)
LinkServiceDep = Depends(get_link_service)
EmbeddingServiceDep = Depends(get_embedding_service)
AgentRunServiceDep = Depends(get_agent_run_service)
VersionHistoryServiceDep = Depends(get_version_history_service)
CurrentUser = Depends(get_current_user)
