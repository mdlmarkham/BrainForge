"""Research Run ORM model for automated content discovery and evaluation."""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseEntity, ProvenanceMixin


class ResearchRun(BaseEntity, ProvenanceMixin):
    """SQLAlchemy ORM model for research_runs table."""

    __tablename__ = "research_runs"

    research_topic = Column(Text, nullable=False)
    research_parameters = Column(JSONB, nullable=False, server_default='{}')
    status = Column(String(20), nullable=False, server_default='pending')
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_sources_discovered = Column(Integer, nullable=False, server_default='0')
    total_sources_assessed = Column(Integer, nullable=False, server_default='0')
    total_sources_approved = Column(Integer, nullable=False, server_default='0')
    error_details = Column(Text, nullable=True)
    performance_metrics = Column(JSONB, nullable=False, server_default='{}')
