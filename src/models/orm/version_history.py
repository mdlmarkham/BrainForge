"""VersionHistory ORM model for constitutional auditability in BrainForge."""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship

from .base import BaseEntity, ProvenanceMixin


class VersionHistory(BaseEntity, ProvenanceMixin):
    """VersionHistory ORM model for constitutional auditability."""
    
    __tablename__ = "version_history"
    
    note_id = Column(PGUUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    version_metadata = Column(JSONB, nullable=False, server_default='{}')
    changes = Column(JSONB, nullable=False, server_default='{}')
    change_reason = Column(Text, nullable=True)
    
    # Relationships
    note = relationship("Note", back_populates="version_history")
    
    def __repr__(self) -> str:
        return f"<VersionHistory(id={self.id}, note_id={self.note_id}, version={self.version})>"