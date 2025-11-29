"""Research Audit Trail model for tracking researcher agent activities."""

from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class AuditActionType:
    """Audit action type constants."""
    RESEARCH_STARTED = "research_started"
    CONTENT_DISCOVERED = "content_discovered"
    QUALITY_ASSESSED = "quality_assessed"
    REVIEW_ASSIGNED = "review_assigned"
    REVIEW_COMPLETED = "review_completed"
    INTEGRATION_PROPOSED = "integration_proposed"


class ResearchAuditTrail(BaseEntity):
    """Complete record of discovery, evaluation, and decision processes for research activities."""
    
    research_run_id: UUID = Field(..., description="ID of the research run being audited")
    action_type: str = Field(..., description="Type of action performed")
    action_details: dict[str, Any] = Field(default_factory=dict, description="Details of the action")
    performed_by: str = Field(..., description="User or agent who performed the action")
    outcome: str = Field(..., description="Outcome of the action")
    error_details: Optional[str] = Field(default=None, description="Error details if action failed")
    performance_metrics: dict[str, Any] = Field(default_factory=dict, description="Performance metrics for the action")


class ResearchAuditTrailCreate(BaseEntity):
    """Create schema for research audit trail entries."""
    
    research_run_id: UUID = Field(..., description="ID of the research run being audited")
    action_type: str = Field(..., description="Type of action performed")
    action_details: dict[str, Any] = Field(default_factory=dict, description="Details of the action")
    performed_by: str = Field(..., description="User or agent who performed the action")
    outcome: str = Field(..., description="Outcome of the action")
    error_details: Optional[str] = Field(default=None, description="Error details if action failed")
    performance_metrics: dict[str, Any] = Field(default_factory=dict, description="Performance metrics for the action")


class ResearchAuditTrailUpdate(BaseEntity):
    """Update schema for research audit trail entries."""
    
    action_type: Optional[str] = Field(default=None, description="Type of action performed")
    action_details: Optional[dict[str, Any]] = Field(default=None, description="Details of the action")
    performed_by: Optional[str] = Field(default=None, description="User or agent who performed the action")
    outcome: Optional[str] = Field(default=None, description="Outcome of the action")
    error_details: Optional[str] = Field(default=None, description="Error details if action failed")
    performance_metrics: Optional[dict[str, Any]] = Field(default=None, description="Performance metrics for the action")