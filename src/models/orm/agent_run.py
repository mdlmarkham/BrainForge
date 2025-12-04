"""AgentRun ORM model for AI agent audit trails in BrainForge."""

from enum import Enum as PyEnum

from sqlalchemy import JSON, CheckConstraint, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import BaseEntity


class AgentRunStatus(PyEnum):
    """Status of agent runs."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING_REVIEW = "pending_review"


class ReviewStatus(PyEnum):
    """Status of human reviews."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class AgentRunORM(BaseEntity):
    """AgentRun ORM model for audit trails."""

    __tablename__ = "agent_runs"

    agent_name = Column(String(255), nullable=False)
    agent_version = Column(String(100), nullable=False)
    input_parameters = Column(JSON, nullable=False, server_default='{}')
    output_note_ids = Column(ARRAY(PGUUID(as_uuid=True)), nullable=False, server_default='{}')
    status = Column(Enum(AgentRunStatus, name="agent_run_status"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default='now()')
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(Text, nullable=True)
    human_reviewer = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_status = Column(Enum(ReviewStatus, name="review_status"), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'pending_review')",
            name="ck_agent_run_status"
        ),
        CheckConstraint(
            "review_status IN ('approved', 'rejected', 'needs_revision') OR review_status IS NULL",
            name="ck_review_status"
        ),
    )

    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, agent={self.agent_name}, status={self.status})>"
