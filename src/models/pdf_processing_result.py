"""PDF processing result model for BrainForge ingestion pipeline."""

from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field

from .base import BaseEntity, TimestampMixin


class PDFProcessingResultBase(TimestampMixin):
    """Base PDF processing result model with constitutional compliance fields."""

    ingestion_task_id: UUID = Field(..., description="Reference to parent IngestionTask")
    extracted_text: str = Field(..., description="Full text extracted from PDF")
    text_quality_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Quality metrics (character count, word count, extraction confidence)"
    )
    section_breaks: dict[str, Any] = Field(
        default_factory=dict,
        description="Document structure (page breaks, section headers)"
    )
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")
    dockling_version: str = Field(..., description="Version of dockling used")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        # Ensure quality metrics have required fields
        if 'character_count' not in self.text_quality_metrics:
            self.text_quality_metrics['character_count'] = len(self.extracted_text)
        if 'word_count' not in self.text_quality_metrics:
            self.text_quality_metrics['word_count'] = len(self.extracted_text.split())


class PDFProcessingResultCreate(PDFProcessingResultBase):
    """Model for creating new PDF processing results."""

    pass


class PDFProcessingResultUpdate(PDFProcessingResultBase):
    """Model for updating existing PDF processing results."""

    pass


class PDFProcessingResult(PDFProcessingResultBase, BaseEntity):
    """Complete PDF processing result model with all constitutional compliance fields."""

    model_config = ConfigDict(from_attributes=True)
