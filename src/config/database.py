"""Database configuration for BrainForge with async SQLAlchemy support."""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

# Import all ORM models to ensure they are registered with Base
from ..models.orm import note, embedding, link, agent_run, version_history
from ..models.orm.base import Base


class DatabaseConfig:
    """Database configuration with environment-driven URLs and connection pooling."""
    
    def __init__(self) -> None:
        self.database_url = self._get_database_url()
        self.engine = create_async_engine(
            self.database_url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
        )
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    def _get_database_url(self) -> str:
        """Get database URL from environment with test override support."""
        # Use test database URL if available
        test_url = os.getenv("TEST_DATABASE_URL")
        if test_url:
            return test_url
        
        # Use main database URL
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Convert sync URL to async URL if needed
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        return database_url
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all database tables (for testing)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session for dependency injection."""
        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()


# Global database configuration instance
db_config = DatabaseConfig()