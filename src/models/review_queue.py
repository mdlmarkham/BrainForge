"""Review queue model for BrainForge ingestion pipeline."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from .base import BaseEntity, TimestampMixin


class ReviewStatus(str, Enum):
    """Review status for content in the review queue."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewQueueBase(TimestampMixin):
    """Base review queue model with constitutional compliance fields."""

    ingestion_task_id: UUID = Field(..., description="Reference to parent IngestionTask")
    review_status: ReviewStatus = Field(default=ReviewStatus.PENDING, description="Current review status")
    reviewer_id: Optional[str] = Field(None, description="ID of human reviewer")
    reviewed_at: Optional[datetime] = Field(None, description="When content was reviewed")
    review_notes: Optional[str] = Field(None, description="Reviewer notes and feedback")
    priority: int = Field(default=0, description="Review priority (higher = more urgent)")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        # If reviewed, ensure reviewer and timestamp are set
        if self.review_status != ReviewStatus.PENDING and not self.reviewer_id:
            raise ValueError("Reviewer ID must be set for non-pending review status")
        if self.review_status != ReviewStatus.PENDING and not self.reviewed_at:
            self.reviewed_at = datetime.now()


class ReviewQueueCreate(ReviewQueueBase):
    """Model for creating new review queue entries."""

    pass


class ReviewQueueUpdate(ReviewQueueBase):
    """Model for updating existing review queue entries."""

    pass


class ReviewQueue(ReviewQueueBase, BaseEntity):
    """Complete review queue model with all constitutional compliance fields."""

    model_config = ConfigDict(from_attributes=True)