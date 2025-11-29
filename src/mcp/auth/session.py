"""MCP Session Management"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from ...models.mcp_session import MCPSessionCreate, MCPSession, MCPSessionUpdate
from ...models.mcp_execution import MCPExecutionCreate, MCPExecution, MCPExecutionUpdate
from ...services.database import DatabaseService


class SessionManager:
    """Manages MCP sessions and execution audit trails"""
    
    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        self.logger = logging.getLogger(__name__)
    
    async def create_session(self, session_create: MCPSessionCreate) -> MCPSession:
        """Create a new MCP session"""
        async with self.database_service.session() as session:
            db_session = await self.database_service.create(
                session, 
                "mcp_sessions", 
                session_create.dict()
            )
            return MCPSession.from_orm(db_session)
    
    async def get_session(self, session_id: UUID) -> Optional[MCPSession]:
        """Get a session by ID"""
        async with self.database_service.session() as session:
            db_session = await self.database_service.get_by_id(
                session, "mcp_sessions", session_id
            )
            if db_session:
                return MCPSession.from_orm(db_session)
            return None
    
    async def update_session(
        self, 
        session_id: UUID, 
        session_update: MCPSessionUpdate
    ) -> Optional[MCPSession]:
        """Update a session"""
        async with self.database_service.session() as session:
            db_session = await self.database_service.update(
                session, "mcp_sessions", session_id, session_update.dict(exclude_unset=True)
            )
            if db_session:
                return MCPSession.from_orm(db_session)
            return None
    
    async def close_session(self, session_id: UUID) -> Optional[MCPSession]:
        """Close a session"""
        session_update = MCPSessionUpdate(status="closed")
        return await self.update_session(session_id, session_update)
    
    async def create_execution(self, execution_create: MCPExecutionCreate) -> MCPExecution:
        """Create a new execution record"""
        async with self.database_service.session() as session:
            db_execution = await self.database_service.create(
                session, 
                "mcp_executions", 
                execution_create.dict()
            )
            return MCPExecution.from_orm(db_execution)
    
    async def get_execution(self, execution_id: UUID) -> Optional[MCPExecution]:
        """Get an execution by ID"""
        async with self.database_service.session() as session:
            db_execution = await self.database_service.get_by_id(
                session, "mcp_executions", execution_id
            )
            if db_execution:
                return MCPExecution.from_orm(db_execution)
            return None
    
    async def update_execution(
        self, 
        execution_id: UUID, 
        execution_update: MCPExecutionUpdate
    ) -> Optional[MCPExecution]:
        """Update an execution record"""
        async with self.database_service.session() as session:
            db_execution = await self.database_service.update(
                session, "mcp_executions", execution_id, execution_update.dict(exclude_unset=True)
            )
            if db_execution:
                return MCPExecution.from_orm(db_execution)
            return None
    
    async def get_session_executions(
        self, 
        session_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> list[MCPExecution]:
        """Get all executions for a session"""
        async with self.database_service.session() as session:
            db_executions = await self.database_service.get_all(
                session, 
                "mcp_executions", 
                filters={"session_id": session_id},
                limit=limit,
                offset=offset,
                order_by="created_at DESC"
            )
            return [MCPExecution.from_orm(execution) for execution in db_executions]
    
    async def get_active_sessions(self) -> list[MCPSession]:
        """Get all active sessions"""
        async with self.database_service.session() as session:
            db_sessions = await self.database_service.get_all(
                session, 
                "mcp_sessions", 
                filters={"status": "active"}
            )
            return [MCPSession.from_orm(session) for session in db_sessions]
    
    async def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than specified hours"""
        async with self.database_service.session() as session:
            # This would require a more sophisticated query with timestamp comparison
            # For now, we'll implement a basic version
            active_sessions = await self.get_active_sessions()
            # TODO: Implement actual timestamp-based cleanup
            self.logger.info(f"Session cleanup would process {len(active_sessions)} active sessions")