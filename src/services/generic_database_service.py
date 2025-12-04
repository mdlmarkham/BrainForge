"""Generic Database Service for MCP Workflow Integration"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class GenericDatabaseService:
    """Generic database service that supports table-name based operations for MCP workflows"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
        # Ensure we're using asyncpg driver for async operations
        if database_url.startswith("postgresql://") and not database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        self.engine = create_async_engine(database_url)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    def session(self):
        """Return an async session context manager"""
        return self.async_session()
    
    async def create(self, session, table_name: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a record in the specified table"""
        try:
            # Use raw SQL for generic table operations
            columns = ', '.join(data.keys())
            placeholders = ', '.join([f':{key}' for key in data.keys()])
            query = text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING *")
            
            result = await session.execute(query, data)
            await session.commit()
            
            # Convert result to dict
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return {}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create record in {table_name}: {e}")
            raise
    
    async def get_by_id(self, session, table_name: str, record_id: UUID) -> dict[str, Any] | None:
        """Get a record by ID from the specified table"""
        try:
            query = text(f"SELECT * FROM {table_name} WHERE id = :id")
            result = await session.execute(query, {"id": str(record_id)})
            row = result.fetchone()
            
            if row:
                return dict(row._mapping)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get record from {table_name}: {e}")
            return None
    
    async def get_all(self, session, table_name: str, filters: dict[str, Any] = None, 
                     limit: int = 100, order_by: str = None) -> list[dict[str, Any]]:
        """Get all records from the specified table with optional filtering"""
        try:
            where_clause = ""
            params = {}
            
            if filters:
                conditions = [f"{key} = :{key}" for key in filters.keys()]
                where_clause = f"WHERE {' AND '.join(conditions)}"
                params.update(filters)
            
            order_clause = f"ORDER BY {order_by}" if order_by else ""
            limit_clause = f"LIMIT {limit}" if limit else ""
            
            query = text(f"SELECT * FROM {table_name} {where_clause} {order_clause} {limit_clause}")
            result = await session.execute(query, params)
            
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get records from {table_name}: {e}")
            return []
    
    async def update(self, session, table_name: str, record_id: UUID, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a record in the specified table"""
        try:
            # Build SET clause
            set_clause = ', '.join([f"{key} = :{key}" for key in data.keys()])
            query = text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id RETURNING *")
            
            params = data.copy()
            params['id'] = str(record_id)
            
            result = await session.execute(query, params)
            await session.commit()
            
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update record in {table_name}: {e}")
            return None
    
    async def delete(self, session, table_name: str, record_id: UUID) -> bool:
        """Delete a record from the specified table"""
        try:
            query = text(f"DELETE FROM {table_name} WHERE id = :id")
            result = await session.execute(query, {"id": str(record_id)})
            await session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete record from {table_name}: {e}")
            return False


# Update the main DatabaseService to use the generic implementation
class DatabaseService(GenericDatabaseService):
    """Main database service that uses generic implementation for MCP workflows"""
    
    def __init__(self, database_url: str):
        super().__init__(database_url)