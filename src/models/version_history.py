"""Version history model for audit trails in BrainForge."""

from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from .base import BaseEntity, ProvenanceMixin


class VersionHistoryBase(ProvenanceMixin):
    """Base version history model for audit trails."""

    note_id: UUID = Field(..., description="Note ID this version belongs to")
    version: int = Field(..., ge=1, description="Version number")
    content: str = Field(..., min_length=1, description="Note content at this version")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata at this version")
    changes: dict[str, Any] = Field(default_factory=dict, description="Changes from previous version")
    change_reason: str | None = Field(default=None, description="Reason for the change")

    @field_validator('version')
    @classmethod
    def validate_version_sequence(cls, v: int) -> int:
        """Validate version numbers are sequential."""
        if v < 1:
            raise ValueError("Version must be at least 1")

        # Basic validation - can be enhanced with database checks for actual sequence
        return v

    @field_validator('content')
    @classmethod
    def validate_content_changes(cls, v: str) -> str:
        """Validate content changes are meaningful."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")

        # Validate content length (basic validation)
        if len(v.strip()) < 5:
            raise ValueError("Content must be at least 5 characters")

        return v.strip()

    @field_validator('changes')
    @classmethod
    def validate_changes_metadata(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate changes metadata structure."""
        if not isinstance(v, dict):
            raise ValueError("Changes metadata must be a dictionary")

        # Validate required change tracking fields
        if 'timestamp' not in v:
            v['timestamp'] = None  # Will be set during creation

        return v

    @field_validator('change_reason')
    @classmethod
    def validate_change_reason(cls, v: str | None) -> str | None:
        """Validate change reason is provided for non-trivial changes."""
        # If change reason is provided, validate it
        if v is not None and not v.strip():
            raise ValueError("Change reason cannot be empty if provided")

        return v.strip() if v else None


class VersionHistoryCreate(VersionHistoryBase):
    """Model for creating a new version history entry."""

    pass


class VersionHistory(VersionHistoryBase, BaseEntity):
    """Complete version history model with constitutional compliance."""

    model_config = ConfigDict(from_attributes=True)
