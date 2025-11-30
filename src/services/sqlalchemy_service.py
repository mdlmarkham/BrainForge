"""SQLAlchemy-based service implementations for BrainForge."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..models.note import Note, NoteCreate, NoteUpdate
from .base import BaseService

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class NoteModel(Base):
    """SQLAlchemy model for notes."""

    __tablename__ = "notes"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(nullable=False)
    note_type: Mapped[str] = mapped_column(nullable=False)
    note_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[str] = mapped_column(nullable=False)
    updated_at: Mapped[str] = mapped_column(nullable=False)
    created_by: Mapped[str] = mapped_column(nullable=False)
    is_ai_generated: Mapped[bool] = mapped_column(default=False)
    ai_justification: Mapped[str] = mapped_column(nullable=True)


class SQLAlchemyService(BaseService):
    """Base service implementation using SQLAlchemy."""

    def __init__(self, database_url: str, model_class: type[Any], pydantic_model: type[Any]):
        self.database_url = database_url
        self.model_class = model_class
        self._pydantic_model = pydantic_model
        self.engine = create_async_engine(database_url)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create(self, data: Any) -> Any:
        """Create a new entity in the database."""
        async with self.async_session() as session:
            # Convert Pydantic model to SQLAlchemy model
            db_model = self.model_class(**data.model_dump())
            session.add(db_model)
            await session.commit()
            await session.refresh(db_model)

            # Convert back to Pydantic model
            return self._to_pydantic(db_model)

    async def get(self, id: UUID) -> Any | None:
        """Get an entity by ID from the database."""
        async with self.async_session() as session:
            stmt = select(self.model_class).where(self.model_class.id == id)
            result = await session.execute(stmt)
            db_model = result.scalar_one_or_none()

            if db_model:
                return self._to_pydantic(db_model)
            return None

    async def list(self, skip: int = 0, limit: int = 100) -> list[Any]:
        """List entities from the database with pagination."""
        async with self.async_session() as session:
            stmt = select(self.model_class).offset(skip).limit(limit)
            result = await session.execute(stmt)
            db_models = result.scalars().all()

            return [self._to_pydantic(model) for model in db_models]

    async def update(self, id: UUID, data: Any) -> Any | None:
        """Update an entity in the database."""
        async with self.async_session() as session:
            # First check if entity exists
            stmt = select(self.model_class).where(self.model_class.id == id)
            result = await session.execute(stmt)
            db_model = result.scalar_one_or_none()

            if not db_model:
                return None

            # Update fields
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_model, field, value)

            await session.commit()
            await session.refresh(db_model)

            return self._to_pydantic(db_model)

    async def delete(self, id: UUID) -> bool:
        """Delete an entity from the database."""
        async with self.async_session() as session:
            stmt = select(self.model_class).where(self.model_class.id == id)
            result = await session.execute(stmt)
            db_model = result.scalar_one_or_none()

            if not db_model:
                return False

            await session.delete(db_model)
            await session.commit()
            return True

    def _to_pydantic(self, db_model: Base) -> Any:
        """Convert SQLAlchemy model to Pydantic model."""
        # This is a simplified conversion - in practice, you'd map fields properly
        model_data = {column.name: getattr(db_model, column.name)
                     for column in db_model.__table__.columns}
        return self._pydantic_model(**model_data)


class SQLAlchemyNoteService(SQLAlchemyService):
    """Note service implementation using SQLAlchemy."""

    def __init__(self, database_url: str):
        super().__init__(database_url, NoteModel, Note)


# Update the database service to use SQLAlchemy implementation
class DatabaseService(SQLAlchemyService):
    """Database service implementation using SQLAlchemy."""

    def __init__(self, database_url: str):
        # Use NoteModel as default for base implementation
        super().__init__(database_url, NoteModel, Note)


class NoteService(DatabaseService):
    """Note-specific database service."""

    async def create(self, data: NoteCreate) -> Note:
        """Create a new note."""
        return await super().create(data)

    async def get(self, id: UUID) -> Note | None:
        """Get a note by ID."""
        return await super().get(id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[Note]:
        """List notes with pagination."""
        return await super().list(skip, limit)

    async def update(self, id: UUID, data: NoteUpdate) -> Note | None:
        """Update a note."""
        return await super().update(id, data)

    async def delete(self, id: UUID) -> bool:
        """Delete a note."""
        return await super().delete(id)
