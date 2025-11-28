"""Note model for BrainForge AI Knowledge Base."""

from enum import Enum
from typing import Any

from pydantic import ConfigDict, Field

from .base import AIGeneratedMixin, BaseEntity, ProvenanceMixin, VersionMixin


class NoteType(str, Enum):
    """Types of notes in the knowledge base."""

    FLEETING = "fleeting"
    LITERATURE = "literature"
    PERMANENT = "permanent"
    INSIGHT = "insight"
    AGENT_GENERATED = "agent_generated"


class NoteBase(ProvenanceMixin, VersionMixin, AIGeneratedMixin):
    """Base note model with constitutional compliance fields."""

    content: str = Field(..., min_length=1, description="Note content (markdown supported)")
    note_type: NoteType = Field(..., description="Type of note")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata fields")

    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate note content is not empty."""
        if not v or not v.strip():
            raise ValueError("Note content cannot be empty")
        return v.strip()


class NoteCreate(NoteBase):
    """Model for creating a new note."""

    pass


class NoteUpdate(NoteBase):
    """Model for updating an existing note."""

    change_reason: str | None = Field(default=None, description="Reason for the change")
    version: int = Field(..., ge=1, description="Current version for optimistic locking")


class Note(NoteBase, BaseEntity):
    """Complete note model with all constitutional compliance fields."""

    model_config = ConfigDict(from_attributes=True)
