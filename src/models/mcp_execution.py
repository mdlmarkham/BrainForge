"""MCP Tool Execution Pydantic Models"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime


class MCPToolExecutionBase(BaseModel):
    """Base MCP tool execution model."""
    
    tool_id: UUID = Field(..., description="Reference to MCP tool")
    session_id: UUID = Field(..., description="MCP session identifier")
    input_parameters: Dict[str, Any] = Field(..., description="Tool input parameters")
    constitutional_compliance: Dict[str, Any] = Field(..., description="Constitutional compliance audit")


class MCPToolExecutionCreate(MCPToolExecutionBase):
    """MCP tool execution creation model."""
    status: str = Field("pending", description="Execution status")
    execution_time_ms: int = Field(0, description="Execution duration in milliseconds")
    
    @validator('status')
    def validate_status(cls, v):
        """Validate execution status."""
        valid_statuses = ["pending", "running", "success", "failed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v
    
    @validator('execution_time_ms')
    def validate_execution_time(cls, v):
        """Validate execution time."""
        if v < 0:
            raise ValueError('Execution time must be non-negative')
        return v


class MCPToolExecutionUpdate(BaseModel):
    """MCP tool execution update model."""
    
    output_result: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    constitutional_compliance: Optional[Dict[str, Any]] = None


class MCPToolExecution(MCPToolExecutionBase):
    """Complete MCP tool execution model with ID and timestamps."""
    
    id: UUID
    output_result: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    execution_time_ms: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True