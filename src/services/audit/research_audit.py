"""Comprehensive audit trail logging for research workflows."""

import logging
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.research_audit_trail import (
    AuditEventType,
    ResearchAuditTrail,
    ResearchAuditTrailCreate,
)
from ...services.sqlalchemy_service import SQLAlchemyService

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """Audit logging levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResearchAuditService(SQLAlchemyService[ResearchAuditTrail]):
    """Service for managing research audit trails."""

    def __init__(self):
        super().__init__(ResearchAuditTrail)

    async def log_event(
        self,
        db: AsyncSession,
        research_run_id: UUID,
        event_type: AuditEventType,
        event_data: dict[str, Any],
        level: AuditLevel = AuditLevel.INFO,
        user_id: UUID | None = None,
        content_source_id: UUID | None = None,
        integration_proposal_id: UUID | None = None,
        review_queue_id: UUID | None = None
    ) -> ResearchAuditTrail:
        """Log an audit event."""

        audit_data = ResearchAuditTrailCreate(
            research_run_id=research_run_id,
            event_type=event_type,
            event_data=event_data,
            level=level.value,
            user_id=user_id,
            content_source_id=content_source_id,
            integration_proposal_id=integration_proposal_id,
            review_queue_id=review_queue_id
        )

        return await self.create(db, audit_data)

    async def get_audit_trail_for_research_run(
        self,
        db: AsyncSession,
        research_run_id: UUID,
        limit: int = 100,
        offset: int = 0,
        event_type: AuditEventType | None = None,
        level: AuditLevel | None = None
    ) -> list[ResearchAuditTrail]:
        """Get audit trail for a specific research run."""

        from sqlalchemy import select

        from ...models.orm.research_audit_trail import (
            ResearchAuditTrail as ResearchAuditTrailORM,
        )

        query = select(ResearchAuditTrailORM).where(
            ResearchAuditTrailORM.research_run_id == research_run_id
        )

        if event_type:
            query = query.where(ResearchAuditTrailORM.event_type == event_type)

        if level:
            query = query.where(ResearchAuditTrailORM.level == level.value)

        query = query.order_by(ResearchAuditTrailORM.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        audits_orm = result.scalars().all()

        return [ResearchAuditTrail.model_validate(audit) for audit in audits_orm]

    async def get_audit_statistics(
        self,
        db: AsyncSession,
        research_run_id: UUID | None = None
    ) -> dict[str, Any]:
        """Get audit statistics."""

        from sqlalchemy import func, select

        from ...models.orm.research_audit_trail import (
            ResearchAuditTrail as ResearchAuditTrailORM,
        )

        base_query = select(ResearchAuditTrailORM)
        if research_run_id:
            base_query = base_query.where(ResearchAuditTrailORM.research_run_id == research_run_id)

        # Count by event type
        event_type_query = (
            select(
                ResearchAuditTrailORM.event_type,
                func.count(ResearchAuditTrailORM.id).label("count")
            )
            .select_from(base_query)
            .group_by(ResearchAuditTrailORM.event_type)
        )

        result = await db.execute(event_type_query)
        event_type_counts = result.mappings().all()

        # Count by level
        level_query = (
            select(
                ResearchAuditTrailORM.level,
                func.count(ResearchAuditTrailORM.id).label("count")
            )
            .select_from(base_query)
            .group_by(ResearchAuditTrailORM.level)
        )

        result = await db.execute(level_query)
        level_counts = result.mappings().all()

        # Total count
        total_query = select(func.count(ResearchAuditTrailORM.id)).select_from(base_query)
        total_result = await db.execute(total_query)
        total_count = total_result.scalar() or 0

        return {
            "total_events": total_count,
            "event_type_counts": {row["event_type"]: row["count"] for row in event_type_counts},
            "level_counts": {row["level"]: row["count"] for row in level_counts},
            "research_run_id": str(research_run_id) if research_run_id else None
        }


class ResearchAuditLogger:
    """High-level audit logger for research workflows."""

    def __init__(self):
        self.audit_service = ResearchAuditService()

    async def log_research_start(self, db: AsyncSession, research_run_id: UUID,
                               search_query: str, user_id: UUID | None = None) -> ResearchAuditTrail:
        """Log research run start."""

        event_data = {
            "search_query": search_query,
            "timestamp": datetime.now().isoformat(),
            "action": "research_started"
        }

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.RESEARCH_START, event_data,
            level=AuditLevel.INFO, user_id=user_id
        )

    async def log_content_discovery(self, db: AsyncSession, research_run_id: UUID,
                                  content_sources_count: int, sources_by_type: dict[str, int],
                                  circuit_breaker_status: dict[str, Any]) -> ResearchAuditTrail:
        """Log content discovery results."""

        event_data = {
            "content_sources_discovered": content_sources_count,
            "sources_by_type": sources_by_type,
            "circuit_breaker_status": circuit_breaker_status,
            "timestamp": datetime.now().isoformat(),
            "action": "content_discovery_completed"
        }

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.CONTENT_DISCOVERY, event_data,
            level=AuditLevel.INFO
        )

    async def log_quality_assessment(self, db: AsyncSession, research_run_id: UUID,
                                   assessments_completed: int, failed_assessments: int,
                                   content_source_id: UUID | None = None) -> ResearchAuditTrail:
        """Log quality assessment results."""

        event_data = {
            "assessments_completed": assessments_completed,
            "failed_assessments": failed_assessments,
            "success_rate": (assessments_completed / (assessments_completed + failed_assessments) * 100
                           if (assessments_completed + failed_assessments) > 0 else 0),
            "timestamp": datetime.now().isoformat(),
            "action": "quality_assessment_completed"
        }

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.QUALITY_ASSESSMENT, event_data,
            level=AuditLevel.INFO, content_source_id=content_source_id
        )

    async def log_integration_proposal(self, db: AsyncSession, research_run_id: UUID,
                                     proposals_generated: int, failed_proposals: int,
                                     content_source_id: UUID | None = None) -> ResearchAuditTrail:
        """Log integration proposal generation."""

        event_data = {
            "proposals_generated": proposals_generated,
            "failed_proposals": failed_proposals,
            "success_rate": (proposals_generated / (proposals_generated + failed_proposals) * 100
                           if (proposals_generated + failed_proposals) > 0 else 0),
            "timestamp": datetime.now().isoformat(),
            "action": "integration_proposal_generated"
        }

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.INTEGRATION_PROPOSAL, event_data,
            level=AuditLevel.INFO, content_source_id=content_source_id
        )

    async def log_review_queue_creation(self, db: AsyncSession, research_run_id: UUID,
                                      queues_created: int, failed_queues: int,
                                      content_source_id: UUID | None = None) -> ResearchAuditTrail:
        """Log review queue creation."""

        event_data = {
            "queues_created": queues_created,
            "failed_queues": failed_queues,
            "success_rate": (queues_created / (queues_created + failed_queues) * 100
                           if (queues_created + failed_queues) > 0 else 0),
            "timestamp": datetime.now().isoformat(),
            "action": "review_queue_created"
        }

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.REVIEW_QUEUE, event_data,
            level=AuditLevel.INFO, content_source_id=content_source_id
        )

    async def log_review_decision(self, db: AsyncSession, research_run_id: UUID,
                                decision: str, implementation_notes: str | None,
                                user_id: UUID, review_queue_id: UUID) -> ResearchAuditTrail:
        """Log review decision."""

        event_data = {
            "decision": decision,
            "implementation_notes": implementation_notes,
            "timestamp": datetime.now().isoformat(),
            "action": "review_decision_made"
        }

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.REVIEW_DECISION, event_data,
            level=AuditLevel.INFO, user_id=user_id, review_queue_id=review_queue_id
        )

    async def log_circuit_breaker_event(self, db: AsyncSession, research_run_id: UUID,
                                      service_name: str, state: str, failure_count: int) -> ResearchAuditTrail:
        """Log circuit breaker state change."""

        event_data = {
            "service_name": service_name,
            "circuit_state": state,
            "failure_count": failure_count,
            "timestamp": datetime.now().isoformat(),
            "action": "circuit_breaker_state_change"
        }

        level = AuditLevel.WARNING if state == "open" else AuditLevel.INFO

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.SYSTEM_EVENT, event_data, level=level
        )

    async def log_error(self, db: AsyncSession, research_run_id: UUID,
                      error_message: str, error_type: str, stack_trace: str | None = None,
                      content_source_id: UUID | None = None) -> ResearchAuditTrail:
        """Log error event."""

        event_data = {
            "error_message": error_message,
            "error_type": error_type,
            "stack_trace": stack_trace,
            "timestamp": datetime.now().isoformat(),
            "action": "error_occurred"
        }

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.ERROR, event_data,
            level=AuditLevel.ERROR, content_source_id=content_source_id
        )

    async def log_recovery_attempt(self, db: AsyncSession, research_run_id: UUID,
                                 failed_step: str, recovery_strategy: str, success: bool) -> ResearchAuditTrail:
        """Log recovery attempt."""

        event_data = {
            "failed_step": failed_step,
            "recovery_strategy": recovery_strategy,
            "recovery_success": success,
            "timestamp": datetime.now().isoformat(),
            "action": "recovery_attempted"
        }

        level = AuditLevel.INFO if success else AuditLevel.WARNING

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.RECOVERY, event_data, level=level
        )

    async def log_performance_metrics(self, db: AsyncSession, research_run_id: UUID,
                                    step_name: str, duration_seconds: float,
                                    resources_used: dict[str, Any]) -> ResearchAuditTrail:
        """Log performance metrics."""

        event_data = {
            "step_name": step_name,
            "duration_seconds": duration_seconds,
            "resources_used": resources_used,
            "timestamp": datetime.now().isoformat(),
            "action": "performance_metrics_recorded"
        }

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.PERFORMANCE, event_data, level=AuditLevel.INFO
        )

    async def log_research_completion(self, db: AsyncSession, research_run_id: UUID,
                                    status: str, summary: dict[str, Any]) -> ResearchAuditTrail:
        """Log research run completion."""

        event_data = {
            "final_status": status,
            "completion_summary": summary,
            "timestamp": datetime.now().isoformat(),
            "action": "research_completed"
        }

        level = AuditLevel.INFO if status == "completed" else AuditLevel.ERROR

        return await self.audit_service.log_event(
            db, research_run_id, AuditEventType.RESEARCH_COMPLETE, event_data, level=level
        )

    async def get_research_timeline(self, db: AsyncSession, research_run_id: UUID) -> list[dict[str, Any]]:
        """Get timeline of events for a research run."""

        audits = await self.audit_service.get_audit_trail_for_research_run(db, research_run_id, limit=1000)

        timeline = []
        for audit in audits:
            timeline.append({
                "timestamp": audit.created_at.isoformat(),
                "event_type": audit.event_type.value,
                "level": audit.level,
                "action": audit.event_data.get("action", "unknown"),
                "data": audit.event_data
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        return timeline

    async def generate_audit_report(self, db: AsyncSession, research_run_id: UUID) -> dict[str, Any]:
        """Generate comprehensive audit report for a research run."""

        # Get audit statistics
        stats = await self.audit_service.get_audit_statistics(db, research_run_id)

        # Get timeline
        timeline = await self.get_research_timeline(db, research_run_id)

        # Calculate metrics
        error_count = stats["level_counts"].get("error", 0)
        warning_count = stats["level_counts"].get("warning", 0)
        total_events = stats["total_events"]

        error_rate = (error_count / total_events * 100) if total_events > 0 else 0
        warning_rate = (warning_count / total_events * 100) if total_events > 0 else 0

        # Find critical events
        critical_events = [event for event in timeline if event["level"] in ["error", "critical"]]

        # Calculate duration if available
        duration = None
        if timeline:
            start_time = datetime.fromisoformat(timeline[0]["timestamp"])
            end_time = datetime.fromisoformat(timeline[-1]["timestamp"])
            duration = (end_time - start_time).total_seconds()

        return {
            "research_run_id": str(research_run_id),
            "report_generated": datetime.now().isoformat(),
            "summary": {
                "total_events": total_events,
                "error_count": error_count,
                "warning_count": warning_count,
                "error_rate": round(error_rate, 2),
                "warning_rate": round(warning_rate, 2),
                "duration_seconds": duration,
                "critical_events_count": len(critical_events)
            },
            "event_breakdown": stats["event_type_counts"],
            "level_breakdown": stats["level_counts"],
            "critical_events": critical_events[:10],  # Top 10 critical events
            "timeline_events_count": len(timeline)
        }


# Global audit logger instance
research_audit_logger = ResearchAuditLogger()
