"""Processing result model for BrainForge ingestion pipeline."""

from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field

from .base import BaseEntity, TimestampMixin


class ProcessingResultBase(TimestampMixin):
    """Base processing result model with constitutional compliance fields."""

    ingestion_task_id: UUID = Field(..., description="Reference to parent IngestionTask")
    summary: str = Field(..., description="Automated summary of ingested content")
    classifications: list[str] = Field(default_factory=list, description="Suggested classifications and tags")
    connection_suggestions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Suggested connections to existing knowledge"
    )
    confidence_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores for automated processing results"
    )
    processing_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional processing metadata and intermediate results"
    )

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        # Ensure confidence scores are within valid range
        for key, score in self.confidence_scores.items():
            if score < 0.0 or score > 1.0:
                raise ValueError(f"Confidence score for '{key}' must be between 0.0 and 1.0")


class ProcessingResultCreate(ProcessingResultBase):
    """Model for creating new processing results."""

    pass


class ProcessingResultUpdate(ProcessingResultBase):
    """Model for updating existing processing results."""

    pass


class ProcessingResult(ProcessingResultBase, BaseEntity):
    """Complete processing result model with all constitutional compliance fields."""

    model_config = ConfigDict(from_attributes=True)
