"""Research Review Queue model for researcher agent content evaluation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base import BaseEntity, TimestampMixin
from .review_queue import ReviewStatus


class ResearchReviewQueueBase(TimestampMixin):
    """Base research review queue model with researcher-specific fields."""

    content_source_id: UUID = Field(..., description="Reference to content source from research")
    review_status: ReviewStatus = Field(default=ReviewStatus.PENDING, description="Current review status")
    reviewer_id: str | None = Field(None, description="ID of human reviewer")
    reviewed_at: datetime | None = Field(None, description="When content was reviewed")
    review_notes: str | None = Field(None, description="Reviewer notes and feedback")
    priority: int = Field(default=0, description="Review priority (higher = more urgent)")
    auto_assessment_summary: str = Field(..., description="Summary of automated quality assessment")
    integration_suggestions: list[dict[str, Any]] = Field(default_factory=list, description="Suggested integration points")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        # If reviewed, ensure reviewer and timestamp are set
        if self.review_status != ReviewStatus.PENDING and not self.reviewer_id:
            raise ValueError("Reviewer ID must be set for non-pending review status")
        if self.review_status != ReviewStatus.PENDING and not self.reviewed_at:
            self.reviewed_at = datetime.now()


class ResearchReviewQueueCreate(ResearchReviewQueueBase):
    """Model for creating new research review queue entries."""

    pass


class ResearchReviewQueueUpdate(ResearchReviewQueueBase):
    """Model for updating existing research review queue entries."""

    pass


class ResearchReviewQueue(ResearchReviewQueueBase, BaseEntity):
    """Complete research review queue model with all constitutional compliance fields."""

    model_config = {"from_attributes": True}
