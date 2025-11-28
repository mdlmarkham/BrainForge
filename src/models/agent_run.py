"""Agent run model for AI agent audit trails in BrainForge."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseEntity


class AgentRunStatus(str, Enum):
    """Status of agent runs."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING_REVIEW = "pending_review"


class ReviewStatus(str, Enum):
    """Status of human reviews."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class AgentRunBase(BaseModel):
    """Base agent run model for audit trails."""

    agent_name: str = Field(..., description="Agent identifier")
    agent_version: str = Field(..., description="Agent version (constitutional requirement)")
    input_parameters: dict = Field(default_factory=dict, description="Agent input data")
    output_note_ids: list[UUID] = Field(default_factory=list, description="Created or modified notes")
    status: AgentRunStatus = Field(..., description="Run status")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = Field(default=None)
    error_details: str | None = Field(default=None)
    human_reviewer: str | None = Field(default=None)
    reviewed_at: datetime | None = Field(default=None)
    review_status: ReviewStatus | None = Field(default=None)

    @classmethod
    def validate_status_transitions(cls, values: dict) -> dict:
        """Validate status transitions follow constitutional workflow."""
        # This will be implemented with actual workflow validation
        # when we have the complete workflow definition
        return values


class AgentRunCreate(AgentRunBase):
    """Model for creating a new agent run."""

    pass


class AgentRun(AgentRunBase, BaseEntity):
    """Complete agent run model with constitutional compliance."""

    model_config = ConfigDict(from_attributes=True)
