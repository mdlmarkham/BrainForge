"""MCP Tool ORM Model"""

from uuid import uuid4

from sqlalchemy import ARRAY, Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.models.orm.base import Base


class MCPTool(Base):
    """MCP Tool ORM model representing tool definitions."""

    __tablename__ = "mcp_tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    input_schema = Column(JSONB, nullable=False)
    output_schema = Column(JSONB, nullable=False)
    tags = Column(ARRAY(String), nullable=True, default=[])
    is_active = Column(Boolean, nullable=False, default=True)
    requires_auth = Column(Boolean, nullable=False, default=True)
    constitutional_gates = Column(ARRAY(String), nullable=True, default=[])
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<MCPTool(id={self.id}, name='{self.name}', is_active={self.is_active})>"

    def to_dict(self):
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'tags': self.tags or [],
            'is_active': self.is_active,
            'requires_auth': self.requires_auth,
            'constitutional_gates': self.constitutional_gates or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
