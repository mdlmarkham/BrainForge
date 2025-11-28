"""Version history model for audit trails in BrainForge."""

from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field

from .base import BaseEntity, ProvenanceMixin


class VersionHistoryBase(ProvenanceMixin):
    """Base version history model for audit trails."""

    note_id: UUID = Field(..., description="Note ID this version belongs to")
    version: int = Field(..., ge=1, description="Version number")
    content: str = Field(..., min_length=1, description="Note content at this version")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata at this version")
    changes: dict[str, Any] = Field(default_factory=dict, description="Changes from previous version")
    change_reason: str | None = Field(default=None, description="Reason for the change")

    @classmethod
    def validate_version_sequence(cls, v: int, values: dict) -> int:
        """Validate version numbers are sequential."""
        # This will be implemented with actual sequence validation
        # when we have access to previous versions
        if v < 1:
            raise ValueError("Version must be at least 1")
        return v


class VersionHistoryCreate(VersionHistoryBase):
    """Model for creating a new version history entry."""

    pass


class VersionHistory(VersionHistoryBase, BaseEntity):
    """Complete version history model with constitutional compliance."""

    model_config = ConfigDict(from_attributes=True)
