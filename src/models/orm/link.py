"""Link ORM model for relationships between notes in BrainForge."""

from enum import Enum as PyEnum

from sqlalchemy import CheckConstraint, Column, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import BaseEntity, ProvenanceMixin


class RelationType(PyEnum):
    """Types of relationships between notes."""

    CITES = "cites"
    SUPPORTS = "supports"
    DERIVED_FROM = "derived_from"
    RELATED = "related"
    CONTRADICTS = "contradicts"


class Link(BaseEntity, ProvenanceMixin):
    """Link ORM model for relationships between notes."""

    __tablename__ = "links"

    source_note_id = Column(PGUUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    target_note_id = Column(PGUUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(Enum(RelationType, name="relation_type"), nullable=False)

    # Relationships
    source_note = relationship("Note", foreign_keys=[source_note_id], back_populates="source_links")
    target_note = relationship("Note", foreign_keys=[target_note_id], back_populates="target_links")

    __table_args__ = (
        CheckConstraint(
            "relation_type IN ('cites', 'supports', 'derived_from', 'related', 'contradicts')",
            name="ck_relation_type"
        ),
        CheckConstraint(
            "source_note_id != target_note_id",
            name="ck_no_self_reference"
        ),
    )

    def __repr__(self) -> str:
        return f"<Link(id={self.id}, source={self.source_note_id}, target={self.target_note_id}, type={self.relation_type})>"
