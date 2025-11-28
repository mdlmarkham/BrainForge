"""Embedding model for vector representations in BrainForge."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseEntity


class EmbeddingBase(BaseModel):
    """Base embedding model for vector representations."""

    note_id: UUID = Field(..., description="Note ID this embedding represents")
    vector: list[float] = Field(..., description="Vector representation of note content")
    model_version: str = Field(..., description="Embedding model version identifier")

    @classmethod
    def validate_vector_dimension(cls, v: list[float], values: dict) -> list[float]:
        """Validate vector dimension matches configured model."""
        # This will be implemented with actual dimension validation
        # when we have the embedding configuration
        if not v:
            raise ValueError("Vector cannot be empty")
        return v


class EmbeddingCreate(EmbeddingBase):
    """Model for creating a new embedding."""

    pass


class Embedding(EmbeddingBase, BaseEntity):
    """Complete embedding model with constitutional compliance."""

    model_config = ConfigDict(from_attributes=True)
