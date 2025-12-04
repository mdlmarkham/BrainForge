"""Agent run model for AI agent audit trails in BrainForge."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

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

    @field_validator('status', 'review_status', 'human_reviewer', 'reviewed_at')
    @classmethod
    def validate_status_transitions(cls, v: Any, info: ValidationInfo) -> Any:
        """Validate status transitions follow constitutional workflow."""
        if info.field_name == 'status':
            current_status = v
            review_status = info.data.get('review_status')
            human_reviewer = info.data.get('human_reviewer')
            reviewed_at = info.data.get('reviewed_at')

            # Validate status transitions
            if current_status == AgentRunStatus.PENDING_REVIEW:
                if review_status is not None:
                    raise ValueError("Cannot set review status while run is pending review")

            elif current_status == AgentRunStatus.SUCCESS:
                if review_status not in [ReviewStatus.APPROVED, None]:
                    raise ValueError("Successful runs must be approved or have no review")

            elif current_status == AgentRunStatus.FAILED:
                if review_status is not None:
                    raise ValueError("Failed runs cannot have review status")

        elif info.field_name == 'review_status':
            if v is not None:
                human_reviewer = info.data.get('human_reviewer')
                reviewed_at = info.data.get('reviewed_at')
                if not human_reviewer:
                    raise ValueError("Review status requires a human reviewer")
                if not reviewed_at:
                    raise ValueError("Review status requires a review timestamp")

        return v

    @field_validator('agent_version')
    @classmethod
    def validate_agent_version_format(cls, v: str) -> str:
        """Validate agent version follows semantic versioning."""
        if not v or not v.strip():
            raise ValueError("Agent version cannot be empty")

        # Basic semantic version validation
        import re
        semver_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$'
        if not re.match(semver_pattern, v.strip()):
            raise ValueError("Agent version must follow semantic versioning format (e.g., 1.0.0)")

        return v.strip()

    @field_validator('input_parameters')
    @classmethod
    def validate_input_parameters(cls, v: dict) -> dict:
        """Validate input parameters structure."""
        if not isinstance(v, dict):
            raise ValueError("Input parameters must be a dictionary")

        # Validate input parameters are JSON-serializable
        import json
        try:
            json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Input parameters must be JSON-serializable: {e}")

        return v

    @field_validator('output_note_ids')
    @classmethod
    def validate_output_note_ids(cls, v: list[UUID]) -> list[UUID]:
        """Validate output note IDs are valid UUIDs."""
        if not isinstance(v, list):
            raise ValueError("Output note IDs must be a list")

        # Validate all elements are UUIDs
        for note_id in v:
            if not isinstance(note_id, UUID):
                raise ValueError("All output note IDs must be valid UUIDs")

        return v


class AgentRunCreate(AgentRunBase):
    """Model for creating a new agent run."""

    pass


class AgentRunResponse(AgentRunBase, BaseEntity):
    """Complete agent run model with constitutional compliance."""

    model_config = ConfigDict(from_attributes=True)
