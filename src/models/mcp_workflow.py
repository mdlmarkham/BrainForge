"""MCP Workflow Pydantic Models"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class MCPWorkflowBase(BaseModel):
    """Base MCP workflow model."""

    workflow_definition: dict[str, Any] = Field(..., description="SpiffWorkflow BPMN definition")
    tool_mappings: dict[str, Any] = Field(..., description="MCP tool to workflow task mappings")
    constitutional_gates: list[str] = Field(default=[], description="Workflow-specific constitutional gates")
    is_active: bool = Field(default=True, description="Workflow activation status")
    version: int = Field(default=1, ge=1, description="Workflow version")

    @validator('workflow_definition')
    def validate_workflow_definition(cls, v):
        """Validate workflow definition format."""
        if not isinstance(v, dict):
            raise ValueError('Workflow definition must be a dictionary')
        if 'process' not in v:
            raise ValueError('Workflow definition must include process definition')
        return v

    @validator('tool_mappings')
    def validate_tool_mappings(cls, v):
        """Validate tool mappings format."""
        if not isinstance(v, dict):
            raise ValueError('Tool mappings must be a dictionary')
        return v

    @validator('version')
    def validate_version(cls, v):
        """Validate version number."""
        if v < 1:
            raise ValueError('Version must be at least 1')
        return v


class MCPWorkflowCreate(MCPWorkflowBase):
    """MCP workflow creation model."""
    pass


class MCPWorkflowUpdate(BaseModel):
    """MCP workflow update model."""

    workflow_definition: dict[str, Any] | None = None
    tool_mappings: dict[str, Any] | None = None
    constitutional_gates: list[str] | None = None
    is_active: bool | None = None
    version: int | None = None


class MCPWorkflow(MCPWorkflowBase):
    """Complete MCP workflow model with ID and timestamps."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
