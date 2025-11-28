"""Link model for relationships between notes in BrainForge."""

from enum import Enum
from uuid import UUID

from pydantic import ConfigDict, Field

from .base import BaseEntity, ProvenanceMixin


class RelationType(str, Enum):
    """Types of relationships between notes."""

    CITES = "cites"
    SUPPORTS = "supports"
    DERIVED_FROM = "derived_from"
    RELATED = "related"
    CONTRADICTS = "contradicts"


class LinkBase(ProvenanceMixin):
    """Base link model for relationships between notes."""

    source_note_id: UUID = Field(..., description="Source note ID")
    target_note_id: UUID = Field(..., description="Target note ID")
    relation_type: RelationType = Field(..., description="Type of relationship")

    @classmethod
    def validate_self_referential(cls, values: dict) -> dict:
        """Validate that source and target are different notes."""
        source_id = values.get('source_note_id')
        target_id = values.get('target_note_id')

        if source_id and target_id and source_id == target_id:
            raise ValueError("Cannot create self-referential links")

        return values


class LinkCreate(LinkBase):
    """Model for creating a new link."""

    pass


class Link(LinkBase, BaseEntity):
    """Complete link model with constitutional compliance."""

    model_config = ConfigDict(from_attributes=True)
