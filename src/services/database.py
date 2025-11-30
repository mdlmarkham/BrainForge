"""Database service implementation for BrainForge with async SQLAlchemy."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.orm.agent_run import AgentRun
from ..models.orm.embedding import Embedding
from ..models.orm.link import Link
from ..models.orm.note import Note
from ..models.orm.version_history import VersionHistory
from .base import BaseService


class NoteService(BaseService[Note]):
    """Note-specific database service."""

    def __init__(self):
        super().__init__(Note)

    async def get_by_type(self, session: AsyncSession, note_type: str, skip: int = 0, limit: int = 100) -> list[Note]:
        """Get notes by type with pagination."""
        stmt = select(Note).where(Note.note_type == note_type).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_ai_generated(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[Note]:
        """Get AI-generated notes with pagination."""
        stmt = select(Note).where(Note.is_ai_generated == True).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()


class LinkService(BaseService[Link]):
    """Link-specific database service."""

    def __init__(self):
        super().__init__(Link)

    async def get_by_source(self, session: AsyncSession, source_note_id: UUID) -> list[Link]:
        """Get links by source note ID."""
        stmt = select(Link).where(Link.source_note_id == source_note_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_target(self, session: AsyncSession, target_note_id: UUID) -> list[Link]:
        """Get links by target note ID."""
        stmt = select(Link).where(Link.target_note_id == target_note_id)
        result = await session.execute(stmt)
        return result.scalars().all()


class EmbeddingService(BaseService[Embedding]):
    """Embedding-specific database service."""

    def __init__(self):
        super().__init__(Embedding)

    async def get_by_note(self, session: AsyncSession, note_id: UUID) -> list[Embedding]:
        """Get embeddings by note ID."""
        stmt = select(Embedding).where(Embedding.note_id == note_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_model_version(self, session: AsyncSession, model_version: str) -> list[Embedding]:
        """Get embeddings by model version."""
        stmt = select(Embedding).where(Embedding.model_version == model_version)
        result = await session.execute(stmt)
        return result.scalars().all()


class AgentRunService(BaseService[AgentRun]):
    """Agent run-specific database service."""

    def __init__(self):
        super().__init__(AgentRun)

    async def get_by_status(self, session: AsyncSession, status: str) -> list[AgentRun]:
        """Get agent runs by status."""
        stmt = select(AgentRun).where(AgentRun.status == status)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_agent(self, session: AsyncSession, agent_name: str, agent_version: str | None = None) -> list[AgentRun]:
        """Get agent runs by agent name and optionally version."""
        stmt = select(AgentRun).where(AgentRun.agent_name == agent_name)
        if agent_version:
            stmt = stmt.where(AgentRun.agent_version == agent_version)
        result = await session.execute(stmt)
        return result.scalars().all()


class VersionHistoryService(BaseService[VersionHistory]):
    """Version history-specific database service."""

    def __init__(self):
        super().__init__(VersionHistory)

    async def get_by_note(self, session: AsyncSession, note_id: UUID) -> list[VersionHistory]:
        """Get version history by note ID."""
        stmt = select(VersionHistory).where(VersionHistory.note_id == note_id).order_by(VersionHistory.version.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_note_and_version(self, session: AsyncSession, note_id: UUID, version: int) -> VersionHistory | None:
        """Get specific version of a note."""
        stmt = select(VersionHistory).where(
            VersionHistory.note_id == note_id,
            VersionHistory.version == version
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class DatabaseService:
    """Main database service that provides access to all entity services."""

    def __init__(self):
        self.note_service = NoteService()
        self.link_service = LinkService()
        self.embedding_service = EmbeddingService()
        self.agent_run_service = AgentRunService()
        self.version_history_service = VersionHistoryService()
