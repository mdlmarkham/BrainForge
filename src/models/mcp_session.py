"""MCP Session Pydantic Models"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime


class MCPSessionBase(BaseModel):
    """Base MCP session model."""
    
    user_id: Optional[UUID] = Field(None, description="Reference to authenticated user")
    agent_id: Optional[UUID] = Field(None, description="Reference to AI agent")
    client_info: Dict[str, Any] = Field(..., description="Client connection information")
    authentication_method: str = Field(..., description="Auth method (jwt, api_key, agent_token)")
    constitutional_context: Dict[str, Any] = Field(..., description="Session-level constitutional context")
    expires_at: Optional[datetime] = Field(None, description="Session expiration timestamp")
    
    @validator('authentication_method')
    def validate_auth_method(cls, v):
        """Validate authentication method."""
        valid_methods = ["jwt", "api_key", "agent_token", "anonymous"]
        if v not in valid_methods:
            raise ValueError(f'Authentication method must be one of: {valid_methods}')
        return v
    
    @validator('client_info')
    def validate_client_info(cls, v):
        """Validate client information."""
        if not isinstance(v, dict):
            raise ValueError('Client info must be a dictionary')
        if 'client_type' not in v:
            raise ValueError('Client info must include client_type')
        return v


class MCPSessionCreate(MCPSessionBase):
    """MCP session creation model."""
    pass


class MCPSessionUpdate(BaseModel):
    """MCP session update model."""
    
    client_info: Optional[Dict[str, Any]] = None
    constitutional_context: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class MCPSession(MCPSessionBase):
    """Complete MCP session model with ID and timestamps."""
    
    id: UUID
    is_active: bool
    last_activity_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True