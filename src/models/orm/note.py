"""Note ORM model for BrainForge."""

from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import Column, String, Text, JSON, Boolean, Integer, CheckConstraint, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .base import BaseEntity, ProvenanceMixin, VersionMixin, AIGeneratedMixin


class NoteType(PyEnum):
    """Types of notes in the knowledge base."""
    
    FLEETING = "fleeting"
    LITERATURE = "literature"
    PERMANENT = "permanent"
    INSIGHT = "insight"
    AGENT_GENERATED = "agent_generated"


class Note(BaseEntity, ProvenanceMixin, VersionMixin, AIGeneratedMixin):
    """Note ORM model with constitutional compliance."""
    
    __tablename__ = "notes"
    
    content = Column(Text, nullable=False)
    note_type = Column(Enum(NoteType, name="note_type"), nullable=False)
    note_metadata = Column(JSONB, nullable=False, server_default='{}')
    
    # Relationships
    embeddings = relationship("Embedding", back_populates="note", cascade="all, delete-orphan")
    source_links = relationship("Link", foreign_keys="Link.source_note_id", back_populates="source_note")
    target_links = relationship("Link", foreign_keys="Link.target_note_id", back_populates="target_note")
    version_history = relationship("VersionHistory", back_populates="note", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            "note_type IN ('fleeting', 'literature', 'permanent', 'insight', 'agent_generated')",
            name="ck_note_type"
        ),
        CheckConstraint(
            "NOT (is_ai_generated AND ai_justification IS NULL)",
            name="ck_ai_justification_required"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Note(id={self.id}, type={self.note_type}, created_by={self.created_by})>"