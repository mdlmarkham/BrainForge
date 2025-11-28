"""Link model for relationships between notes in BrainForge."""

from enum import Enum
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, ValidationInfo

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

    @field_validator('source_note_id', 'target_note_id')
    @classmethod
    def validate_self_referential(cls, v: UUID, info: ValidationInfo) -> UUID:
        """Validate that source and target are different notes."""
        if info.field_name == 'source_note_id':
            target_id = info.data.get('target_note_id')
            if target_id and v == target_id:
                raise ValueError("Cannot create self-referential links")
        elif info.field_name == 'target_note_id':
            source_id = info.data.get('source_note_id')
            if source_id and v == source_id:
                raise ValueError("Cannot create self-referential links")
        return v

    @field_validator('relation_type')
    @classmethod
    def validate_relation_type(cls, v: RelationType) -> RelationType:
        """Validate relation type constraints."""
        # Add business logic for relation type validation if needed
        return v

    @field_validator('provenance')
    @classmethod
    def validate_provenance_metadata(cls, v: dict) -> dict:
        """Validate provenance metadata structure."""
        if not isinstance(v, dict):
            raise ValueError("Provenance must be a dictionary")
        
        # Validate provenance-specific fields
        if 'created_by' not in v:
            raise ValueError("Provenance must include 'created_by' field")
        
        return v


class LinkCreate(LinkBase):
    """Model for creating a new link."""

    pass


class Link(LinkBase, BaseEntity):
    """Complete link model with constitutional compliance."""

    model_config = ConfigDict(from_attributes=True)
