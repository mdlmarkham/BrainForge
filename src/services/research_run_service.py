"""Research Run Service for managing automated content discovery and evaluation."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.research_run import (
    ResearchRun,
    ResearchRunCreate,
    ResearchRunStatus,
    ResearchRunUpdate,
)
from .base import BaseService

logger = logging.getLogger(__name__)


class ResearchRunService(BaseService):
    """Service for managing research runs with business logic."""

    def __init__(self):
        super().__init__(ResearchRun)

    async def create_research_run(
        self,
        session: AsyncSession,
        research_topic: str,
        created_by: str,
        research_parameters: dict | None = None
    ) -> ResearchRun:
        """Create a new research run with initial parameters."""

        research_run_data = ResearchRunCreate(
            research_topic=research_topic,
            research_parameters=research_parameters or {},
            created_by=created_by,
            provenance={"created_by": created_by, "type": "research_run"}
        )

        research_run = await self.create(session, research_run_data.model_dump())
        logger.info(f"Created research run {research_run.id} for topic: {research_topic}")
        return research_run

    async def start_research_run(self, session: AsyncSession, research_run_id: UUID) -> ResearchRun | None:
        """Start a research run by updating its status and setting start time."""

        update_data = ResearchRunUpdate(
            status=ResearchRunStatus.RUNNING,
            started_at=datetime.now()
        )

        research_run = await self.update(session, research_run_id, update_data.model_dump(exclude_unset=True))
        if research_run:
            logger.info(f"Started research run {research_run_id}")
        return research_run

    async def complete_research_run(
        self,
        session: AsyncSession,
        research_run_id: UUID,
        total_sources_discovered: int = 0,
        total_sources_assessed: int = 0,
        total_sources_approved: int = 0,
        performance_metrics: dict | None = None
    ) -> ResearchRun | None:
        """Complete a research run with results and metrics."""

        update_data = ResearchRunUpdate(
            status=ResearchRunStatus.COMPLETED,
            completed_at=datetime.now(),
            total_sources_discovered=total_sources_discovered,
            total_sources_assessed=total_sources_assessed,
            total_sources_approved=total_sources_approved,
            performance_metrics=performance_metrics or {}
        )

        research_run = await self.update(session, research_run_id, update_data.model_dump(exclude_unset=True))
        if research_run:
            logger.info(f"Completed research run {research_run_id} with {total_sources_discovered} sources discovered")
        return research_run

    async def fail_research_run(
        self,
        session: AsyncSession,
        research_run_id: UUID,
        error_details: str
    ) -> ResearchRun | None:
        """Mark a research run as failed with error details."""

        update_data = ResearchRunUpdate(
            status=ResearchRunStatus.FAILED,
            completed_at=datetime.now(),
            error_details=error_details
        )

        research_run = await self.update(session, research_run_id, update_data.model_dump(exclude_unset=True))
        if research_run:
            logger.error(f"Research run {research_run_id} failed: {error_details}")
        return research_run

    async def get_pending_runs(self, session: AsyncSession, limit: int = 10) -> list[ResearchRun]:
        """Get pending research runs that need to be processed."""

        stmt = select(ResearchRun).where(ResearchRun.status == ResearchRunStatus.PENDING).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_running_runs(self, session: AsyncSession) -> list[ResearchRun]:
        """Get currently running research runs."""

        stmt = select(ResearchRun).where(ResearchRun.status == ResearchRunStatus.RUNNING)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update_research_metrics(
        self,
        session: AsyncSession,
        research_run_id: UUID,
        sources_discovered: int = 0,
        sources_assessed: int = 0,
        sources_approved: int = 0
    ) -> ResearchRun | None:
        """Update research run metrics during execution."""

        # Get current research run to calculate incremental updates
        research_run = await self.get(session, research_run_id)
        if not research_run:
            return None

        update_data = ResearchRunUpdate(
            total_sources_discovered=research_run.total_sources_discovered + sources_discovered,
            total_sources_assessed=research_run.total_sources_assessed + sources_assessed,
            total_sources_approved=research_run.total_sources_approved + sources_approved
        )

        return await self.update(session, research_run_id, update_data.model_dump(exclude_unset=True))
