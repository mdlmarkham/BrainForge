"""Alembic environment configuration for BrainForge."""

import os
from logging.config import fileConfig
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import all ORM models to ensure they are registered with Base
from src.models.orm.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Get database URL from environment with async support."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    # Strip any leading/trailing whitespace
    database_url = database_url.strip()

    # Convert sync URL to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncConnection

    async def run_async_migrations():
        """Run migrations in an async context."""
        configuration = config.get_section(config.config_ini_section)
        configuration["sqlalchemy.url"] = get_url()

        connectable = create_async_engine(
            configuration["sqlalchemy.url"],
            poolclass=pool.NullPool,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(
                lambda sync_conn: context.configure(
                    connection=sync_conn, target_metadata=target_metadata
                )
            )

            async with connection.begin() as transaction:
                await connection.run_sync(lambda conn: context.run_migrations())
                await transaction.commit()

    # Run the async migrations
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
