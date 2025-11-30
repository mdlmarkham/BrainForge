"""MCP Tool Pydantic Models"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class MCPToolBase(BaseModel):
    """Base MCP tool model."""

    name: str = Field(..., min_length=3, max_length=255, description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: dict[str, Any] = Field(..., description="JSON Schema for tool inputs")
    output_schema: dict[str, Any] = Field(..., description="JSON Schema for tool outputs")
    tags: list[str] = Field(default=[], max_items=10, description="Tool categorization tags")
    is_active: bool = Field(default=True, description="Tool activation status")
    requires_auth: bool = Field(default=True, description="Whether tool requires authentication")
    constitutional_gates: list[str] = Field(default=[], description="Constitutional gates to enforce")

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

    description: str | None = None
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    tags: list[str] | None = None
    is_active: bool | None = None
    requires_auth: bool | None = None
    constitutional_gates: list[str] | None = None


class MCPTool(MCPToolBase):
    """Complete MCP tool model with ID and timestamps."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
