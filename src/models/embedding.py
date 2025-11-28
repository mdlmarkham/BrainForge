"""Embedding model for vector representations in BrainForge."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import BaseEntity


class EmbeddingBase(BaseModel):
    """Base embedding model for vector representations."""

    note_id: UUID = Field(..., description="Note ID this embedding represents")
    vector: list[float] = Field(..., description="Vector representation of note content")
    model_version: str = Field(..., description="Embedding model version identifier")

    @field_validator('vector')
    @classmethod
    def validate_vector_dimension(cls, v: list[float]) -> list[float]:
        """Validate vector dimension matches configured model."""
        if not v:
            raise ValueError("Vector cannot be empty")
        
        # Validate vector dimensions (basic validation - can be enhanced with config)
        if len(v) == 0:
            raise ValueError("Vector must have at least one dimension")
        
        # Validate all elements are numeric
        for i, value in enumerate(v):
            if not isinstance(value, (int, float)):
                raise ValueError(f"Vector element at index {i} must be numeric")
        
        return v

    @field_validator('model_version')
    @classmethod
    def validate_model_version(cls, v: str) -> str:
        """Validate embedding model version format."""
        if not v or not v.strip():
            raise ValueError("Model version cannot be empty")
        
        # Basic validation for model version format
        if len(v.strip()) < 3:
            raise ValueError("Model version must be at least 3 characters")
        
        return v.strip()

    @field_validator('note_id')
    @classmethod
    def validate_note_id_reference(cls, v: UUID) -> UUID:
        """Validate note ID reference exists (placeholder for future implementation)."""
        # This will be enhanced with actual database validation
        return v


class EmbeddingCreate(EmbeddingBase):
    """Model for creating a new embedding."""

    pass


class Embedding(EmbeddingBase, BaseEntity):
    """Complete embedding model with constitutional compliance."""

    model_config = ConfigDict(from_attributes=True)
