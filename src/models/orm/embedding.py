"""Embedding ORM model for vector representations in BrainForge."""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import BaseEntity


class Embedding(BaseEntity):
    """Embedding ORM model for vector representations."""
    
    __tablename__ = "embeddings"
    
    note_id = Column(PGUUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    vector = Column(Vector(1536), nullable=True)  # Configurable dimension
    model_version = Column(String(100), nullable=False)
    
    # Relationships
    note = relationship("Note", back_populates="embeddings")
    
    def __repr__(self) -> str:
        return f"<Embedding(id={self.id}, note_id={self.note_id}, model={self.model_version})>"