"""MCP Workflow ORM Model"""

from sqlalchemy import Column, Integer, Boolean, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from uuid import uuid4

from src.models.orm.base import Base


class MCPWorkflow(Base):
    """MCP Workflow ORM model representing workflow definitions."""
    
    __tablename__ = "mcp_workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_definition = Column(JSONB, nullable=False)
    tool_mappings = Column(JSONB, nullable=False)
    constitutional_gates = Column(ARRAY(String), nullable=True, default=[])
    is_active = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<MCPWorkflow(id={self.id}, version={self.version}, is_active={self.is_active})>"
    
    def to_dict(self):
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'workflow_definition': self.workflow_definition,
            'tool_mappings': self.tool_mappings,
            'constitutional_gates': self.constitutional_gates or [],
            'is_active': self.is_active,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def increment_version(self):
        """Increment workflow version."""
        self.version += 1