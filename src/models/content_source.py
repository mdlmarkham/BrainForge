"""Content Source model for external content discovered by researcher agent."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class ContentSourceType:
    """Content source type constants."""
    WEB_ARTICLE = "web_article"
    ACADEMIC_PAPER = "academic_paper"
    NEWS_REPORT = "news_report"
    BLOG_POST = "blog_post"
    TECHNICAL_DOCUMENT = "technical_document"


class ContentSource(BaseEntity):
    """Represents external content discovered by the researcher agent."""

    research_run_id: UUID = Field(..., description="ID of the research run that discovered this source")
    source_type: str = Field(..., description="Type of content source")
    source_url: str = Field(..., description="URL or identifier of the source")
    source_title: str = Field(..., description="Title of the content")
    source_metadata: dict[str, str] = Field(default_factory=dict, description="Metadata about the source")
    retrieval_method: str = Field(..., description="Method used to retrieve the content")
    retrieval_timestamp: datetime = Field(..., description="When the content was retrieved")
    content_hash: str = Field(..., description="Hash of the content for deduplication")
    raw_content: str | None = Field(default=None, description="Raw content text")
    is_duplicate: bool = Field(default=False, description="Whether this is a duplicate of another source")
    duplicate_of: UUID | None = Field(default=None, description="ID of the original source if duplicate")


class ContentSourceCreate(BaseEntity):
    """Create schema for content sources."""

    research_run_id: UUID = Field(..., description="ID of the research run that discovered this source")
    source_type: str = Field(..., description="Type of content source")
    source_url: str = Field(..., description="URL or identifier of the source")
    source_title: str = Field(..., description="Title of the content")
    source_metadata: dict[str, str] = Field(default_factory=dict, description="Metadata about the source")
    retrieval_method: str = Field(..., description="Method used to retrieve the content")
    retrieval_timestamp: datetime = Field(..., description="When the content was retrieved")
    content_hash: str = Field(..., description="Hash of the content for deduplication")
    raw_content: str | None = Field(default=None, description="Raw content text")


class ContentSourceUpdate(BaseEntity):
    """Update schema for content sources."""

    source_type: str | None = Field(default=None, description="Type of content source")
    source_title: str | None = Field(default=None, description="Title of the content")
    source_metadata: dict[str, str] | None = Field(default=None, description="Metadata about the source")
    raw_content: str | None = Field(default=None, description="Raw content text")
    is_duplicate: bool | None = Field(default=None, description="Whether this is a duplicate of another source")
    duplicate_of: UUID | None = Field(default=None, description="ID of the original source if duplicate")
