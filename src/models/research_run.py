"""Research Run model for automated content discovery and evaluation."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from .base import BaseEntity, ProvenanceMixin


class ResearchRunStatus:
    """Research run status constants."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchRun(BaseEntity, ProvenanceMixin):
    """Represents a single research execution with parameters, results, and metadata."""
    
    research_topic: str = Field(..., description="Topic or query for research")
    research_parameters: dict[str, Any] = Field(default_factory=dict, description="Research configuration parameters")
    status: str = Field(default=ResearchRunStatus.PENDING, description="Current status of the research run")
    started_at: Optional[datetime] = Field(default=None, description="When the research run started")
    completed_at: Optional[datetime] = Field(default=None, description="When the research run completed")
    total_sources_discovered: int = Field(default=0, ge=0, description="Total sources discovered")
    total_sources_assessed: int = Field(default=0, ge=0, description="Total sources quality assessed")
    total_sources_approved: int = Field(default=0, ge=0, description="Total sources approved for integration")
    error_details: Optional[str] = Field(default=None, description="Error details if research failed")
    performance_metrics: dict[str, Any] = Field(default_factory=dict, description="Performance metrics for the run")


class ResearchRunCreate(BaseEntity, ProvenanceMixin):
    """Create schema for research runs."""
    
    research_topic: str = Field(..., description="Topic or query for research")
    research_parameters: dict[str, Any] = Field(default_factory=dict, description="Research configuration parameters")


class ResearchRunUpdate(BaseEntity):
    """Update schema for research runs."""
    
    research_topic: Optional[str] = Field(default=None, description="Topic or query for research")
    research_parameters: Optional[dict[str, Any]] = Field(default=None, description="Research configuration parameters")
    status: Optional[str] = Field(default=None, description="Current status of the research run")
    started_at: Optional[datetime] = Field(default=None, description="When the research run started")
    completed_at: Optional[datetime] = Field(default=None, description="When the research run completed")
    total_sources_discovered: Optional[int] = Field(default=None, ge=0, description="Total sources discovered")
    total_sources_assessed: Optional[int] = Field(default=None, ge=0, description="Total sources quality assessed")
    total_sources_approved: Optional[int] = Field(default=None, ge=0, description="Total sources approved for integration")
    error_details: Optional[str] = Field(default=None, description="Error details if research failed")
    performance_metrics: Optional[dict[str, Any]] = Field(default=None, description="Performance metrics for the run")