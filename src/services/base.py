"""Base service implementation with async SQLAlchemy support."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.orm.base import Base

T = TypeVar("T", bound=Base)


class BaseService(Generic[T]):
    """Base service class for async SQLAlchemy operations."""

    def __init__(self, model_class: type[T]):
        self.model_class = model_class

    async def create(self, session: AsyncSession, data: dict[str, Any]) -> T:
        """Create a new entity in the database."""
        instance = self.model_class(**data)
        session.add(instance)
        await session.commit()
        await session.refresh(instance)
        return instance

    async def get(self, session: AsyncSession, id: UUID) -> T | None:
        """Get an entity by ID from the database."""
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[T]:
        """List entities from the database with pagination."""
        stmt = select(self.model_class).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(self, session: AsyncSession, id: UUID, data: dict[str, Any]) -> T | None:
        """Update an entity in the database."""
        instance = await self.get(session, id)
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
            await session.commit()
            await session.refresh(instance)
        return instance

    async def delete(self, session: AsyncSession, id: UUID) -> bool:
        """Delete an entity from the database."""
        instance = await self.get(session, id)
        if instance:
            await session.delete(instance)
            await session.commit()
            return True
        return False
