"""MCP Session ORM Model"""

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.models.orm.base import Base


class MCPSession(Base):
    """MCP Session ORM model representing active MCP sessions."""

    __tablename__ = "mcp_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agent_runs.id'), nullable=True)
    client_info = Column(JSONB, nullable=False)
    authentication_method = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_activity_at = Column(DateTime, nullable=False, server_default=func.now())
    constitutional_context = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="mcp_sessions")
    agent = relationship("AgentRun", backref="mcp_sessions")
    tool_executions = relationship("MCPToolExecution", back_populates="session")

    def __repr__(self):
        return f"<MCPSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"

    def to_dict(self):
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'agent_id': str(self.agent_id) if self.agent_id else None,
            'client_info': self.client_info,
            'authentication_method': self.authentication_method,
            'is_active': self.is_active,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'constitutional_context': self.constitutional_context,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    def is_expired(self):
        """Check if the session has expired."""
        if not self.expires_at:
            return False
        from datetime import datetime
        return datetime.now() > self.expires_at

    def refresh_activity(self):
        """Update last activity timestamp."""
        from datetime import datetime
        self.last_activity_at = datetime.now()
