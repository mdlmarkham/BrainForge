"""Base SQLAlchemy ORM model with constitutional compliance."""

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin for timestamp fields."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ProvenanceMixin:
    """Mixin for provenance tracking (constitutional requirement)."""

    created_by = Column(String(255), nullable=False)
    provenance = Column(JSONB, nullable=False, server_default='{}')


class VersionMixin:
    """Mixin for version tracking (constitutional requirement)."""

    version = Column(Integer, nullable=False, server_default='1')


class AIGeneratedMixin:
    """Mixin for AI-generated content tracking (constitutional requirement)."""

    is_ai_generated = Column(Boolean, nullable=False, server_default='false')
    ai_justification = Column(Text, nullable=True)


class BaseEntity(Base, TimestampMixin):
    """Base entity with common fields for all database entities."""

    __abstract__ = True

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
