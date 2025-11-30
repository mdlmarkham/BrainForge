"""Research orchestrator with comprehensive failure handling and recovery mechanisms."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.content_source import ContentSource
from ..models.research_run import ResearchRun, ResearchRunStatus
from ..services.content_discovery_service import ContentDiscoveryService
from ..services.external.circuit_breaker import CircuitBreakerError, get_circuit_breaker
from ..services.integration_proposal_service import IntegrationProposalService
from ..services.quality_assessment_service import QualityAssessmentService
from ..services.research_run_service import ResearchRunService
from ..services.review_queue_service import ReviewQueueService

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Orchestrates research workflows with comprehensive failure handling."""

    def __init__(self):
        self.research_service = ResearchRunService()
        self.discovery_service = ContentDiscoveryService()
        self.quality_service = QualityAssessmentService()
        self.integration_service = IntegrationProposalService()
        self.review_service = ReviewQueueService()

        # Circuit breakers for external services
        self.google_circuit = get_circuit_breaker("google_search")
        self.semantic_circuit = get_circuit_breaker("semantic_scholar")
        self.news_circuit = get_circuit_breaker("news_api")
        self.ai_circuit = get_circuit_breaker("ai_service")

    async def execute_research_run(self, db: AsyncSession, research_run_id: UUID) -> ResearchRun:
        """Execute a complete research run with failure handling."""

        try:
            # Get the research run
            research_run = await self.research_service.get(db, research_run_id)
            if not research_run:
                raise ValueError(f"Research run {research_run_id} not found")

            # Update status to running
            await self.research_service.update_status(db, research_run_id, ResearchRunStatus.RUNNING)

            # Execute research workflow
            result = await self._execute_workflow(db, research_run)

            # Update final status
            final_status = ResearchRunStatus.COMPLETED if result["success"] else ResearchRunStatus.FAILED
            await self.research_service.update_status(db, research_run_id, final_status, result.get("error_message"))

            logger.info(f"Research run {research_run_id} completed with status: {final_status.value}")
            return await self.research_service.get(db, research_run_id)

        except Exception as e:
            logger.error(f"Research run {research_run_id} failed: {e}")
            await self._handle_critical_failure(db, research_run_id, str(e))
            raise

    async def _execute_workflow(self, db: AsyncSession, research_run: ResearchRun) -> dict[str, Any]:
        """Execute the research workflow with step-by-step failure handling."""

        workflow_steps = [
            ("content_discovery", self._execute_content_discovery),
            ("quality_assessment", self._execute_quality_assessment),
            ("integration_proposal", self._execute_integration_proposal),
            ("review_queue", self._execute_review_queue)
        ]

        results = {
            "success": True,
            "steps_completed": [],
            "steps_failed": [],
            "error_message": None,
            "recovery_attempted": False
        }

        for step_name, step_function in workflow_steps:
            try:
                step_result = await step_function(db, research_run)
                results["steps_completed"].append({
                    "step": step_name,
                    "result": step_result,
                    "success": True
                })
                logger.info(f"Research step '{step_name}' completed for run {research_run.id}")

            except Exception as e:
                logger.error(f"Research step '{step_name}' failed for run {research_run.id}: {e}")
                results["steps_failed"].append({
                    "step": step_name,
                    "error": str(e),
                    "success": False
                })

                # Attempt recovery for critical steps
                if step_name in ["content_discovery", "quality_assessment"]:
                    recovery_success = await self._attempt_recovery(db, research_run, step_name, e)
                    if recovery_success:
                        results["recovery_attempted"] = True
                        results["success"] = True  # Mark as successful if recovery worked
                        continue

                # If recovery failed or not attempted, mark overall as failed
                results["success"] = False
                results["error_message"] = f"Step '{step_name}' failed: {e}"
                break

        return results

    async def _execute_content_discovery(self, db: AsyncSession, research_run: ResearchRun) -> dict[str, Any]:
        """Execute content discovery with circuit breaker protection."""

        # Check circuit breaker status
        if self.google_circuit.is_open() and self.semantic_circuit.is_open() and self.news_circuit.is_open():
            raise CircuitBreakerError("All external discovery services are unavailable")

        try:
            content_sources = await self.discovery_service.discover_content(
                db, research_run.id, research_run.search_query, research_run.search_filters
            )

            return {
                "content_sources_discovered": len(content_sources),
                "sources_by_type": self._categorize_content_sources(content_sources),
                "circuit_breaker_status": self._get_discovery_circuit_status()
            }

        except CircuitBreakerError:
            raise
        except Exception as e:
            # Record failure in circuit breakers
            self._record_discovery_failure(e)
            raise

    async def _execute_quality_assessment(self, db: AsyncSession, research_run: ResearchRun) -> dict[str, Any]:
        """Execute quality assessment with failure handling."""

        # Get content sources for this research run
        content_sources = await self.research_service.get_content_sources_for_run(db, research_run.id)

        if not content_sources:
            return {"assessments_completed": 0, "error": "No content sources to assess"}

        assessments_completed = 0
        failed_assessments = 0

        for content_source in content_sources:
            try:
                # Check AI service circuit breaker
                if self.ai_circuit.is_open():
                    logger.warning(f"AI service circuit breaker open, skipping assessment for {content_source.id}")
                    continue

                assessment = await self.quality_service.assess_content_quality(db, content_source.id)
                assessments_completed += 1

                # Record success
                self.ai_circuit.record_success()

            except Exception as e:
                failed_assessments += 1
                logger.error(f"Quality assessment failed for content source {content_source.id}: {e}")

                # Record failure
                self.ai_circuit.record_failure()

        return {
            "assessments_completed": assessments_completed,
            "failed_assessments": failed_assessments,
            "total_content_sources": len(content_sources),
            "ai_circuit_status": self.ai_circuit.get_state_info()
        }

    async def _execute_integration_proposal(self, db: AsyncSession, research_run: ResearchRun) -> dict[str, Any]:
        """Execute integration proposal generation."""

        content_sources = await self.research_service.get_content_sources_for_run(db, research_run.id)

        if not content_sources:
            return {"proposals_generated": 0, "error": "No content sources for integration"}

        proposals_generated = 0
        failed_proposals = 0

        for content_source in content_sources:
            try:
                proposal = await self.integration_service.generate_integration_proposal(
                    db, content_source.id, research_run.id
                )
                proposals_generated += 1

            except Exception as e:
                failed_proposals += 1
                logger.error(f"Integration proposal generation failed for content source {content_source.id}: {e}")

        return {
            "proposals_generated": proposals_generated,
            "failed_proposals": failed_proposals,
            "total_content_sources": len(content_sources)
        }

    async def _execute_review_queue(self, db: AsyncSession, research_run: ResearchRun) -> dict[str, Any]:
        """Execute review queue creation."""

        content_sources = await self.research_service.get_content_sources_for_run(db, research_run.id)

        if not content_sources:
            return {"review_queues_created": 0, "error": "No content sources for review"}

        queues_created = 0
        failed_queues = 0

        for content_source in content_sources:
            try:
                # Only create review queue if there's a quality assessment
                assessment = await self.quality_service.get_assessment_by_content_source(db, content_source.id)
                if assessment:
                    review_queue = await self.review_service.create_review_queue_for_content(
                        db, content_source.id, research_run.id
                    )
                    queues_created += 1

            except Exception as e:
                failed_queues += 1
                logger.error(f"Review queue creation failed for content source {content_source.id}: {e}")

        return {
            "review_queues_created": queues_created,
            "failed_queues": failed_queues,
            "total_content_sources": len(content_sources)
        }

    async def _attempt_recovery(self, db: AsyncSession, research_run: ResearchRun,
                              failed_step: str, error: Exception) -> bool:
        """Attempt to recover from a failed research step."""

        logger.info(f"Attempting recovery for failed step '{failed_step}' in research run {research_run.id}")

        recovery_strategies = {
            "content_discovery": self._recover_content_discovery,
            "quality_assessment": self._recover_quality_assessment
        }

        if failed_step in recovery_strategies:
            try:
                return await recovery_strategies[failed_step](db, research_run, error)
            except Exception as recovery_error:
                logger.error(f"Recovery attempt failed for step '{failed_step}': {recovery_error}")

        return False

    async def _recover_content_discovery(self, db: AsyncSession, research_run: ResearchRun,
                                       error: Exception) -> bool:
        """Recover from content discovery failure."""

        # Strategy 1: Try alternative search parameters
        try:
            # Simplify search query
            simplified_query = self._simplify_search_query(research_run.search_query)
            alternative_sources = await self.discovery_service.discover_content(
                db, research_run.id, simplified_query, {}
            )

            if alternative_sources:
                logger.info(f"Recovery successful: Found {len(alternative_sources)} sources with simplified query")
                return True

        except Exception as e:
            logger.warning(f"Alternative search parameters recovery failed: {e}")

        # Strategy 2: Use fallback data sources
        try:
            # Try with only one service at a time
            fallback_sources = await self._discover_with_fallback_services(db, research_run)
            if fallback_sources:
                logger.info(f"Recovery successful: Found {len(fallback_sources)} sources with fallback services")
                return True

        except Exception as e:
            logger.warning(f"Fallback services recovery failed: {e}")

        return False

    async def _recover_quality_assessment(self, db: AsyncSession, research_run: ResearchRun,
                                        error: Exception) -> bool:
        """Recover from quality assessment failure."""

        # Strategy: Skip AI-based assessment and use basic scoring
        try:
            content_sources = await self.research_service.get_content_sources_for_run(db, research_run.id)

            for content_source in content_sources:
                # Create basic quality assessment without AI
                basic_assessment = await self.quality_service.create_basic_assessment(db, content_source.id)
                if basic_assessment:
                    logger.info(f"Created basic assessment for content source {content_source.id}")

            return True

        except Exception as e:
            logger.warning(f"Basic assessment recovery failed: {e}")
            return False

    def _simplify_search_query(self, query: str) -> str:
        """Simplify a search query for recovery purposes."""
        # Basic simplification - take first few words
        words = query.split()
        return " ".join(words[:3]) if len(words) > 3 else query

    async def _discover_with_fallback_services(self, db: AsyncSession, research_run: ResearchRun) -> list[ContentSource]:
        """Discover content using fallback services one at a time."""

        fallback_services = [
            ("google_search", lambda: self.discovery_service.search_google(research_run.search_query)),
            ("semantic_scholar", lambda: self.discovery_service.search_semantic_scholar(research_run.search_query)),
            ("news_api", lambda: self.discovery_service.search_news(research_run.search_query))
        ]

        for service_name, discovery_func in fallback_services:
            circuit = get_circuit_breaker(service_name)
            if not circuit.is_open():
                try:
                    sources = await discovery_func()
                    if sources:
                        # Save these sources to the research run
                        for source_data in sources:
                            await self.discovery_service.save_content_source(db, source_data, research_run.id)
                        return await self.research_service.get_content_sources_for_run(db, research_run.id)
                except Exception as e:
                    logger.warning(f"Fallback service {service_name} failed: {e}")
                    circuit.record_failure()

        return []

    def _categorize_content_sources(self, content_sources: list[ContentSource]) -> dict[str, int]:
        """Categorize content sources by type."""
        categories = {}
        for source in content_sources:
            category = source.source_type or "unknown"
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _get_discovery_circuit_status(self) -> dict[str, Any]:
        """Get discovery service circuit breaker status."""
        return {
            "google_search": self.google_circuit.get_state_info(),
            "semantic_scholar": self.semantic_circuit.get_state_info(),
            "news_api": self.news_circuit.get_state_info()
        }

    def _record_discovery_failure(self, error: Exception):
        """Record failure in discovery circuit breakers."""
        # Determine which service likely failed based on error message
        error_str = str(error).lower()

        if "google" in error_str:
            self.google_circuit.record_failure()
        elif "semantic" in error_str:
            self.semantic_circuit.record_failure()
        elif "news" in error_str:
            self.news_circuit.record_failure()
        else:
            # Record in all circuits if uncertain
            self.google_circuit.record_failure()
            self.semantic_circuit.record_failure()
            self.news_circuit.record_failure()

    async def _handle_critical_failure(self, db: AsyncSession, research_run_id: UUID, error_message: str):
        """Handle critical failure of a research run."""

        try:
            # Update research run status to failed
            await self.research_service.update_status(
                db, research_run_id, ResearchRunStatus.FAILED, error_message
            )

            # Log critical failure details
            logger.critical(f"Research run {research_run_id} failed critically: {error_message}")

            # TODO: Implement notification system for critical failures
            # await self._notify_administrators(research_run_id, error_message)

        except Exception as e:
            logger.error(f"Failed to handle critical failure for research run {research_run_id}: {e}")

    async def get_research_run_health(self, db: AsyncSession, research_run_id: UUID) -> dict[str, Any]:
        """Get health status of a research run."""

        research_run = await self.research_service.get(db, research_run_id)
        if not research_run:
            return {"error": "Research run not found"}

        content_sources = await self.research_service.get_content_sources_for_run(db, research_run_id)
        proposals = await self.integration_service.get_proposals_for_research_run(db, research_run_id)
        review_queues = await self.review_service.get_review_queues_for_research_run(db, research_run_id)

        return {
            "research_run_id": str(research_run_id),
            "status": research_run.status.value,
            "content_sources_count": len(content_sources),
            "integration_proposals_count": len(proposals),
            "review_queues_count": len(review_queues),
            "circuit_breaker_status": self._get_discovery_circuit_status(),
            "health_score": self._calculate_health_score(research_run, content_sources, proposals, review_queues)
        }

    def _calculate_health_score(self, research_run: ResearchRun, content_sources: list[ContentSource],
                              proposals: list, review_queues: list) -> float:
        """Calculate a health score for the research run."""

        base_score = 0.0

        # Status-based scoring
        status_scores = {
            ResearchRunStatus.COMPLETED: 1.0,
            ResearchRunStatus.RUNNING: 0.7,
            ResearchRunStatus.PENDING: 0.3,
            ResearchRunStatus.FAILED: 0.0
        }
        base_score = status_scores.get(research_run.status, 0.0)

        # Content-based scoring (only for running/completed runs)
        if research_run.status in [ResearchRunStatus.RUNNING, ResearchRunStatus.COMPLETED]:
            if content_sources:
                base_score += 0.2
            if proposals:
                base_score += 0.3
            if review_queues:
                base_score += 0.2

        return min(1.0, base_score)
