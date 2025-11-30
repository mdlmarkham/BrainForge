"""Ingestion task model for BrainForge ingestion pipeline."""

from datetime import datetime
from enum import Enum

from pydantic import ConfigDict, Field, field_validator

from .base import BaseEntity, ProvenanceMixin, TimestampMixin


class ContentType(str, Enum):
    """Types of content that can be ingested."""

    WEB = "web"
    VIDEO = "video"
    TEXT = "text"
    PDF = "pdf"


class ProcessingState(str, Enum):
    """Processing states for ingestion tasks."""

    VALIDATING = "validating"
    EXTRACTING_METADATA = "extracting_metadata"
    EXTRACTING_TEXT = "extracting_text"
    ASSESSING_QUALITY = "assessing_quality"
    SUMMARIZING = "summarizing"
    CLASSIFYING = "classifying"
    AWAITING_REVIEW = "awaiting_review"
    INTEGRATED = "integrated"
    FAILED = "failed"


class IngestionTaskBase(ProvenanceMixin, TimestampMixin):
    """Base ingestion task model with constitutional compliance fields."""

    content_type: ContentType = Field(..., description="Type of content being ingested")
    source_url: str | None = Field(None, description="Original source URL")
    file_name: str | None = Field(None, description="File name for uploaded content")
    file_size: int | None = Field(None, ge=0, description="File size in bytes")
    tags: list[str] = Field(default_factory=list, description="Initial tags for classification")
    priority: str = Field(default="normal", description="Processing priority")
    processing_state: ProcessingState = Field(default=ProcessingState.VALIDATING, description="Current processing state")
    processing_attempts: int = Field(default=0, ge=0, description="Number of processing attempts")
    last_processing_error: str | None = Field(None, description="Last error message if processing failed")
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority values."""
        valid_priorities = {'low', 'normal', 'high'}
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v

    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v: int | None) -> int | None:
        """Validate file size constraints."""
        if v is not None:
            # PDF files must be ≤ 100MB
            if v > 100 * 1024 * 1024:
                raise ValueError("PDF file too large (>100MB)")
        return v

    @field_validator('processing_attempts')
    @classmethod
    def validate_processing_attempts(cls, v: int) -> int:
        """Validate processing attempts don't exceed maximum."""
        if v > 3:
            raise ValueError("Maximum processing attempts exceeded")
        return v


class IngestionTaskCreate(IngestionTaskBase):
    """Model for creating new ingestion tasks."""

    pass


class IngestionTaskUpdate(IngestionTaskBase):
    """Model for updating existing ingestion tasks."""

    pass


class IngestionTask(IngestionTaskBase, BaseEntity):
    """Complete ingestion task model with all constitutional compliance fields."""

    model_config = ConfigDict(from_attributes=True)
