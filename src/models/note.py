"""Note model for BrainForge AI Knowledge Base."""

from enum import Enum
from typing import Any

from pydantic import ConfigDict, Field, field_validator

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

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate note content is not empty."""
        if not v or not v.strip():
            raise ValueError("Note content cannot be empty")
        return v.strip()

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata structure and content."""
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        
        # Validate metadata keys and values
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Metadata keys must be strings")
            if not isinstance(value, (str, int, float, bool, list, dict)) and value is not None:
                raise ValueError(f"Metadata value for key '{key}' must be a valid JSON type")
        
        return v

    @field_validator('note_type')
    @classmethod
    def validate_note_type(cls, v: NoteType) -> NoteType:
        """Validate note type transitions and constraints."""
        # Add business logic for note type transitions if needed
        return v


class NoteCreate(NoteBase):
    """Model for creating a new note."""

    pass


class NoteUpdate(NoteBase):
    """Model for updating an existing note."""

    change_reason: str | None = Field(default=None, description="Reason for the change")
    version: int = Field(default=1, ge=1, description="Current version for optimistic locking")


class Note(NoteBase, BaseEntity):
    """Complete note model with all constitutional compliance fields."""

    model_config = ConfigDict(from_attributes=True)
