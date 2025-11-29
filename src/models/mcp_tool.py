"""MCP Tool Pydantic Models"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime


class MCPToolBase(BaseModel):
    """Base MCP tool model."""
    
    name: str = Field(..., min_length=3, max_length=255, description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="JSON Schema for tool inputs")
    output_schema: Dict[str, Any] = Field(..., description="JSON Schema for tool outputs")
    tags: List[str] = Field(default=[], max_items=10, description="Tool categorization tags")
    is_active: bool = Field(default=True, description="Tool activation status")
    requires_auth: bool = Field(default=True, description="Whether tool requires authentication")
    constitutional_gates: List[str] = Field(default=[], description="Constitutional gates to enforce")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate tool name format."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Tool name must contain only alphanumeric characters and underscores')
        return v
    
    @validator('input_schema', 'output_schema')
    def validate_schema(cls, v):
        """Validate JSON schema format."""
        if not isinstance(v, dict):
            raise ValueError('Schema must be a dictionary')
        if 'type' not in v:
            raise ValueError('Schema must have a type field')
        return v


class MCPToolCreate(MCPToolBase):
    """MCP tool creation model."""
    pass


class MCPToolUpdate(BaseModel):
    """MCP tool update model."""
    
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    requires_auth: Optional[bool] = None
    constitutional_gates: Optional[List[str]] = None


class MCPTool(MCPToolBase):
    """Complete MCP tool model with ID and timestamps."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True