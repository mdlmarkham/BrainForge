"""Content source model for BrainForge ingestion pipeline."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from .base import BaseEntity, TimestampMixin


class ContentSourceBase(TimestampMixin):
    """Base content source model with constitutional compliance fields."""

    ingestion_task_id: UUID = Field(..., description="Reference to parent IngestionTask")
    source_type: str = Field(..., description="Type of source (web, video, pdf, etc.)")
    source_url: Optional[str] = Field(None, description="Original source URL")
    source_metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Source-specific metadata and retrieval information"
    )
    retrieval_method: str = Field(..., description="Method used to retrieve content")
    retrieval_timestamp: datetime = Field(..., description="When content was retrieved")
    content_hash: str = Field(..., description="Hash of original content for deduplication")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        # Ensure retrieval timestamp is set if not provided
        if not self.retrieval_timestamp:
            self.retrieval_timestamp = datetime.now()


class ContentSourceCreate(ContentSourceBase):
    """Model for creating new content sources."""

    pass


class ContentSourceUpdate(ContentSourceBase):
    """Model for updating existing content sources."""

    pass


class ContentSource(ContentSourceBase, BaseEntity):
    """Complete content source model with all constitutional compliance fields."""

    model_config = ConfigDict(from_attributes=True)