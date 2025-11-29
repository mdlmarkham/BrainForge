"""Integration Proposal model for suggesting content integration into knowledge base."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class IntegrationProposalStatus:
    """Integration proposal status constants."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    INTEGRATED = "integrated"


class IntegrationProposal(BaseEntity):
    """Represents suggested connections and classifications for new content within existing knowledge."""
    
    content_source_id: UUID = Field(..., description="ID of the content source being proposed for integration")
    proposal_status: str = Field(default=IntegrationProposalStatus.PENDING_REVIEW, description="Current proposal status")
    proposed_note_content: str = Field(..., description="Proposed content for the new note")
    proposed_tags: list[str] = Field(default_factory=list, description="Suggested tags for the content")
    connection_suggestions: list[dict[str, Any]] = Field(default_factory=list, description="Suggested connections to existing notes")
    integration_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in integration quality")
    integration_metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata about the integration proposal")
    integrated_note_id: Optional[UUID] = Field(default=None, description="ID of the integrated note if approved")
    integration_timestamp: Optional[datetime] = Field(default=None, description="When the content was integrated")


class IntegrationProposalCreate(BaseEntity):
    """Create schema for integration proposals."""
    
    content_source_id: UUID = Field(..., description="ID of the content source being proposed for integration")
    proposed_note_content: str = Field(..., description="Proposed content for the new note")
    proposed_tags: list[str] = Field(default_factory=list, description="Suggested tags for the content")
    connection_suggestions: list[dict[str, Any]] = Field(default_factory=list, description="Suggested connections to existing notes")
    integration_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in integration quality")
    integration_metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata about the integration proposal")


class IntegrationProposalUpdate(BaseEntity):
    """Update schema for integration proposals."""
    
    proposal_status: Optional[str] = Field(default=None, description="Current proposal status")
    proposed_note_content: Optional[str] = Field(default=None, description="Proposed content for the new note")
    proposed_tags: Optional[list[str]] = Field(default=None, description="Suggested tags for the content")
    connection_suggestions: Optional[list[dict[str, Any]]] = Field(default=None, description="Suggested connections to existing notes")
    integration_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence in integration quality")
    integration_metadata: Optional[dict[str, Any]] = Field(default=None, description="Metadata about the integration proposal")
    integrated_note_id: Optional[UUID] = Field(default=None, description="ID of the integrated note if approved")
    integration_timestamp: Optional[datetime] = Field(default=None, description="When the content was integrated")