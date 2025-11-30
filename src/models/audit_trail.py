"""Audit trail model for BrainForge ingestion pipeline."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field

from .base import BaseEntity, TimestampMixin


class AuditTrailBase(TimestampMixin):
    """Base audit trail model with constitutional compliance fields."""

    ingestion_task_id: UUID = Field(..., description="Reference to parent IngestionTask")
    action_type: str = Field(..., description="Type of action performed")
    action_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed information about the action"
    )
    performed_by: str = Field(..., description="User or agent who performed the action")
    outcome: str = Field(..., description="Outcome of the action (success, failure, etc.)")
    error_details: str | None = Field(None, description="Error details if action failed")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        # Ensure action details contain required information
        if 'timestamp' not in self.action_details:
            self.action_details['timestamp'] = datetime.now().isoformat()


class AuditTrailCreate(AuditTrailBase):
    """Model for creating new audit trail entries."""

    pass


class AuditTrailUpdate(AuditTrailBase):
    """Model for updating existing audit trail entries."""

    pass


class AuditTrail(AuditTrailBase, BaseEntity):
    """Complete audit trail model with all constitutional compliance fields."""

    model_config = ConfigDict(from_attributes=True)
