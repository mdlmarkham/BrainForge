"""Base model definitions for BrainForge entities with constitutional compliance."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class BrainForgeBaseModel(BaseModel):
    """Base model for all BrainForge entities with constitutional compliance."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True, validate_assignment=True)


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator('updated_at', mode='before')
    @classmethod
    def update_timestamp(cls, v: datetime | None) -> datetime:
        """Update timestamp when model is modified."""
        return v or datetime.now()


class ProvenanceMixin(BaseModel):
    """Mixin for provenance tracking (constitutional requirement)."""

    created_by: str = Field(..., description="User or agent identifier")
    provenance: dict[str, Any] = Field(default_factory=dict)

    @field_validator('provenance')
    @classmethod
    def validate_provenance(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate provenance metadata structure."""
        if not isinstance(v, dict):
            raise ValueError("Provenance must be a dictionary")
        return v


class VersionMixin(BaseModel):
    """Mixin for version tracking (constitutional requirement)."""

    version: int = Field(default=1, ge=1)

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: int) -> int:
        """Validate version number."""
        if v < 1:
            raise ValueError("Version must be at least 1")
        return v


class AIGeneratedMixin(BaseModel):
    """Mixin for AI-generated content tracking (constitutional requirement)."""

    is_ai_generated: bool = Field(default=False)
    ai_justification: str | None = Field(default=None)

    @field_validator('ai_justification')
    @classmethod
    def validate_ai_justification(cls, v: str | None, info: ValidationInfo) -> str | None:
        """Validate AI justification is provided for AI-generated content."""
        is_ai_generated = info.data.get('is_ai_generated', False)
        if is_ai_generated and not v:
            raise ValueError("AI-generated content must include justification")
        return v


class BaseEntity(BrainForgeBaseModel, TimestampMixin):
    """Base entity with common fields for all database entities."""

    id: UUID = Field(default_factory=uuid4)

    def __hash__(self) -> int:
        """Make entities hashable by their ID."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Compare entities by their ID."""
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id
