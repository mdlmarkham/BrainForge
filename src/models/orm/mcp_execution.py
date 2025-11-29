"""MCP Tool Execution ORM Model"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from src.models.orm.base import Base


class MCPToolExecution(Base):
    """MCP Tool Execution ORM model representing tool execution history."""
    
    __tablename__ = "mcp_tool_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tool_id = Column(UUID(as_uuid=True), ForeignKey('mcp_tools.id'), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey('mcp_sessions.id'), nullable=False)
    input_parameters = Column(JSONB, nullable=False)
    output_result = Column(JSONB, nullable=True)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=False, default=0)
    constitutional_compliance = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    tool = relationship("MCPTool", backref="executions")
    session = relationship("MCPSession", back_populates="tool_executions")
    
    def __repr__(self):
        return f"<MCPToolExecution(id={self.id}, tool_id={self.tool_id}, status='{self.status}')>"
    
    def to_dict(self):
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'tool_id': str(self.tool_id),
            'session_id': str(self.session_id),
            'input_parameters': self.input_parameters,
            'output_result': self.output_result,
            'status': self.status,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms,
            'constitutional_compliance': self.constitutional_compliance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def mark_completed(self, result=None, error_message=None, execution_time_ms=0):
        """Mark execution as completed with result or error."""
        from datetime import datetime
        self.completed_at = datetime.now()
        self.execution_time_ms = execution_time_ms
        
        if error_message:
            self.status = "failed"
            self.error_message = error_message
        else:
            self.status = "success"
            self.output_result = result
    
    def mark_cancelled(self):
        """Mark execution as cancelled."""
        from datetime import datetime
        self.status = "cancelled"
        self.completed_at = datetime.now()