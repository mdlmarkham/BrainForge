"""Integration Proposal model for suggesting content integration into knowledge base."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class IntegrationProposalStatus:
    """Integration proposal status constants."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    INTEGRATED = "integrated"
    IMPLEMENTED = "implemented"


# Alias for backward compatibility
ProposalStatus = IntegrationProposalStatus


class IntegrationProposal(BaseEntity):
    """Represents suggested connections and classifications for new content within existing knowledge."""

    content_source_id: UUID = Field(..., description="ID of the content source being proposed for integration")
    proposal_status: str = Field(default=IntegrationProposalStatus.PENDING_REVIEW, description="Current proposal status")
    proposed_note_content: str = Field(..., description="Proposed content for the new note")
    proposed_tags: list[str] = Field(default_factory=list, description="Suggested tags for the content")
    connection_suggestions: list[dict[str, Any]] = Field(default_factory=list, description="Suggested connections to existing notes")
    integration_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in integration quality")
    integration_metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata about the integration proposal")
    integrated_note_id: UUID | None = Field(default=None, description="ID of the integrated note if approved")
    integration_timestamp: datetime | None = Field(default=None, description="When the content was integrated")


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

    proposal_status: str | None = Field(default=None, description="Current proposal status")
    proposed_note_content: str | None = Field(default=None, description="Proposed content for the new note")
    proposed_tags: list[str] | None = Field(default=None, description="Suggested tags for the content")
    connection_suggestions: list[dict[str, Any]] | None = Field(default=None, description="Suggested connections to existing notes")
    integration_confidence: float | None = Field(default=None, ge=0.0, le=1.0, description="Confidence in integration quality")
    integration_metadata: dict[str, Any] | None = Field(default=None, description="Metadata about the integration proposal")
    integrated_note_id: UUID | None = Field(default=None, description="ID of the integrated note if approved")
    integration_timestamp: datetime | None = Field(default=None, description="When the content was integrated")
