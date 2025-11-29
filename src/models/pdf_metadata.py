"""PDF metadata model for BrainForge ingestion pipeline."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from .base import BaseEntity, TimestampMixin


class PDFMetadataBase(TimestampMixin):
    """Base PDF metadata model with constitutional compliance fields."""

    ingestion_task_id: UUID = Field(..., description="Reference to parent IngestionTask")
    page_count: int = Field(..., ge=1, description="Number of pages in PDF")
    author: Optional[str] = Field(None, description="Document author from metadata")
    title: Optional[str] = Field(None, description="Document title from metadata")
    subject: Optional[str] = Field(None, description="Document subject from metadata")
    creation_date: Optional[datetime] = Field(None, description="PDF creation date")
    modification_date: Optional[datetime] = Field(None, description="PDF modification date")
    pdf_version: str = Field(..., description="PDF version (e.g., '1.4', '1.7')")
    encryption_status: str = Field(..., description="Encryption status ('none', 'password', 'certificate')")
    extraction_method: str = Field(..., description="Text extraction method used ('dockling_basic', 'dockling_advanced')")
    extraction_quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score of text extraction (0.0-1.0)")

    @field_validator('encryption_status')
    @classmethod
    def validate_encryption_status(cls, v: str) -> str:
        """Validate encryption status values."""
        valid_statuses = {'none', 'password', 'certificate'}
        if v not in valid_statuses:
            raise ValueError(f"Encryption status must be one of {valid_statuses}")
        return v

    @field_validator('extraction_method')
    @classmethod
    def validate_extraction_method(cls, v: str) -> str:
        """Validate extraction method values."""
        valid_methods = {'dockling_basic', 'dockling_advanced'}
        if v not in valid_methods:
            raise ValueError(f"Extraction method must be one of {valid_methods}")
        return v

    @field_validator('extraction_quality_score')
    @classmethod
    def validate_quality_score(cls, v: float) -> float:
        """Validate quality score is within valid range."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Quality score must be between 0.0 and 1.0")
        return v


class PDFMetadataCreate(PDFMetadataBase):
    """Model for creating new PDF metadata."""

    pass


class PDFMetadataUpdate(PDFMetadataBase):
    """Model for updating existing PDF metadata."""

    pass


class PDFMetadata(PDFMetadataBase, BaseEntity):
    """Complete PDF metadata model with all constitutional compliance fields."""

    model_config = ConfigDict(from_attributes=True)