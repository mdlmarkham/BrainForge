"""Review processor service for handling review decisions and integration workflows."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.content_source import ContentSource
from ..models.integration_proposal import IntegrationProposal, IntegrationProposalCreate
from ..models.quality_assessment import QualityAssessment
from ..models.research_review_queue import ResearchReviewQueue, ReviewStatus
from ..services.integration_proposal_service import IntegrationProposalService
from ..services.quality_assessment_service import QualityAssessmentService
from ..services.review_queue_service import ReviewQueueService

logger = logging.getLogger(__name__)


class ReviewProcessor:
    """Processes review decisions and manages integration workflows."""

    def __init__(self):
        self.review_queue_service = ReviewQueueService()
        self.integration_proposal_service = IntegrationProposalService()
        self.quality_assessment_service = QualityAssessmentService()

    async def process_review_decision(self, db: AsyncSession, review_id: UUID,
                                    decision: ReviewStatus, notes: str = None) -> dict[str, Any]:
        """Process a review decision and trigger appropriate workflows."""

        try:
            # Get the review
            review = await self.review_queue_service.get(db, review_id)
            if not review:
                raise ValueError(f"Review {review_id} not found")

            # Update review status
            updated_review = await self.review_queue_service.update_review_status(
                db, review_id, decision, notes
            )

            # Process based on decision
            result = {
                "review_id": str(review_id),
                "decision": decision,
                "review_updated": True
            }

            if decision == ReviewStatus.APPROVED:
                # Generate integration proposal for approved content
                integration_proposal = await self._generate_integration_proposal(db, review)
                result["integration_proposal_created"] = True
                result["integration_proposal_id"] = str(integration_proposal.id)

            elif decision == ReviewStatus.REJECTED:
                # Handle rejected content (could trigger re-assessment or archiving)
                await self._handle_rejected_content(db, review)
                result["rejection_processed"] = True

            logger.info(f"Processed review decision {decision} for review {review_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to process review decision for {review_id}: {e}")
            raise

    async def _generate_integration_proposal(self, db: AsyncSession, review: ResearchReviewQueue) -> IntegrationProposal:
        """Generate an integration proposal for approved content."""

        try:
            # Get content source and quality assessment
            content_source = await self._get_content_source(db, review.content_source_id)
            quality_assessment = await self.quality_assessment_service.get_quality_assessment_for_source(
                db, review.content_source_id
            )

            if not content_source:
                raise ValueError(f"Content source {review.content_source_id} not found")

            # Create integration proposal
            proposal_data = IntegrationProposalCreate(
                content_source_id=review.content_source_id,
                research_run_id=review.research_run_id,
                proposal_type="knowledge_integration",
                integration_strategy=self._determine_integration_strategy(content_source, quality_assessment),
                proposed_actions=self._generate_proposed_actions(content_source, quality_assessment),
                estimated_effort=self._estimate_integration_effort(content_source, quality_assessment),
                confidence_score=self._calculate_integration_confidence(content_source, quality_assessment),
                proposal_metadata={
                    "review_id": str(review.id),
                    "quality_score": quality_assessment.overall_score if quality_assessment else 0.5,
                    "content_type": content_source.source_type
                }
            )

            integration_proposal = await self.integration_proposal_service.create(db, proposal_data)

            logger.info(f"Generated integration proposal {integration_proposal.id} for content source {review.content_source_id}")
            return integration_proposal

        except Exception as e:
            logger.error(f"Failed to generate integration proposal for review {review.id}: {e}")
            raise

    async def _get_content_source(self, db: AsyncSession, content_source_id: UUID) -> ContentSource | None:
        """Get content source by ID."""

        from sqlalchemy import select

        from ..models.orm.content_source import ContentSource as ContentSourceORM

        result = await db.execute(
            select(ContentSourceORM).where(ContentSourceORM.id == content_source_id)
        )
        content_source_orm = result.scalar_one_or_none()

        if content_source_orm:
            return ContentSource.model_validate(content_source_orm)
        return None

    def _determine_integration_strategy(self, content_source: ContentSource,
                                      quality_assessment: QualityAssessment | None) -> str:
        """Determine the appropriate integration strategy based on content characteristics."""

        if not quality_assessment:
            return "basic_integration"

        # Strategy based on quality score and content type
        overall_score = quality_assessment.overall_score

        if overall_score >= 0.8:
            return "comprehensive_integration"
        elif overall_score >= 0.6:
            return "standard_integration"
        else:
            return "basic_integration"

    def _generate_proposed_actions(self, content_source: ContentSource,
                                 quality_assessment: QualityAssessment | None) -> dict[str, Any]:
        """Generate proposed integration actions."""

        actions = {
            "summary_creation": True,
            "tagging": True,
            "categorization": True,
            "relationship_mapping": quality_assessment.overall_score >= 0.7 if quality_assessment else False,
            "cross_referencing": quality_assessment.overall_score >= 0.8 if quality_assessment else False,
            "quality_annotation": True
        }

        # Adjust actions based on content type
        if content_source.source_type in ["research_paper", "academic_article"]:
            actions["methodology_extraction"] = True
            actions["citation_analysis"] = True

        return actions

    def _estimate_integration_effort(self, content_source: ContentSource,
                                   quality_assessment: QualityAssessment | None) -> str:
        """Estimate the effort required for integration."""

        # Simple estimation based on content characteristics
        if not quality_assessment:
            return "medium"

        overall_score = quality_assessment.overall_score

        if overall_score >= 0.8:
            return "low"  # High quality content is easier to integrate
        elif overall_score >= 0.6:
            return "medium"
        else:
            return "high"  # Low quality requires more processing

    def _calculate_integration_confidence(self, content_source: ContentSource,
                                        quality_assessment: QualityAssessment | None) -> float:
        """Calculate confidence score for integration success."""

        if not quality_assessment:
            return 0.5

        # Confidence based on quality scores
        base_confidence = quality_assessment.overall_score

        # Adjust based on content type and completeness
        if content_source.source_type in ["research_paper", "academic_article"]:
            base_confidence += 0.1  # Structured content is easier to integrate

        if quality_assessment.completeness_score >= 0.7:
            base_confidence += 0.1  # Complete content integrates better

        return min(1.0, max(0.0, base_confidence))

    async def _handle_rejected_content(self, db: AsyncSession, review: ResearchReviewQueue) -> None:
        """Handle content that was rejected during review."""

        # Log rejection for audit purposes
        logger.info(f"Content source {review.content_source_id} rejected in review {review.id}")

        # Could trigger re-assessment or archiving workflows
        # For now, just log the rejection

        # Example: Could set a flag to prevent re-submission
        # or trigger a re-assessment with different parameters

    async def batch_process_reviews(self, db: AsyncSession, review_decisions: dict[UUID, ReviewStatus]) -> dict[str, Any]:
        """Process multiple review decisions in batch."""

        results = {
            "processed": [],
            "failed": [],
            "total": len(review_decisions)
        }

        for review_id, decision in review_decisions.items():
            try:
                result = await self.process_review_decision(db, review_id, decision)
                results["processed"].append({
                    "review_id": str(review_id),
                    "decision": decision,
                    "result": result
                })
            except Exception as e:
                logger.error(f"Failed to process review {review_id}: {e}")
                results["failed"].append({
                    "review_id": str(review_id),
                    "decision": decision,
                    "error": str(e)
                })

        logger.info(f"Batch processed {len(results['processed'])} reviews, {len(results['failed'])} failed")
        return results

    async def get_review_workflow_status(self, db: AsyncSession, research_run_id: UUID) -> dict[str, Any]:
        """Get comprehensive status of the review workflow for a research run."""

        # Get review statistics
        review_stats = await self.review_queue_service.get_review_statistics(db, research_run_id)

        # Get integration proposals generated
        integration_proposals = await self.integration_proposal_service.get_proposals_for_research_run(db, research_run_id)

        # Calculate workflow completion percentage
        total_reviews = review_stats.get("total_reviews", 0)
        completed_reviews = sum(
            count for status, count in review_stats.get("status_counts", {}).items()
            if status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]
        )

        completion_percentage = (completed_reviews / total_reviews * 100) if total_reviews > 0 else 0

        return {
            "research_run_id": str(research_run_id),
            "review_statistics": review_stats,
            "integration_proposals_generated": len(integration_proposals),
            "workflow_completion_percentage": round(completion_percentage, 2),
            "average_review_time_minutes": review_stats.get("average_review_time_minutes", 0),
            "status_breakdown": review_stats.get("status_counts", {})
        }

    async def escalate_review(self, db: AsyncSession, review_id: UUID,
                            escalation_reason: str, escalated_to: str) -> ResearchReviewQueue:
        """Escalate a review to a different reviewer or supervisor."""

        try:
            review = await self.review_queue_service.get(db, review_id)
            if not review:
                raise ValueError(f"Review {review_id} not found")

            # Update review with escalation information
            update_data = {
                "assigned_to": escalated_to,
                "status": ReviewStatus.ESCALATED,
                "review_notes": f"ESCALATED: {escalation_reason}. Previous notes: {review.review_notes or 'None'}"
            }

            escalated_review = await self.review_queue_service.update(db, review_id, update_data)

            logger.info(f"Escalated review {review_id} to {escalated_to}")
            return escalated_review

        except Exception as e:
            logger.error(f"Failed to escalate review {review_id}: {e}")
            raise

    async def reassign_review(self, db: AsyncSession, review_id: UUID,
                            new_reviewer: str, reassignment_reason: str) -> ResearchReviewQueue:
        """Reassign a review to a different reviewer."""

        try:
            review = await self.review_queue_service.get(db, review_id)
            if not review:
                raise ValueError(f"Review {review_id} not found")

            # Reassign the review
            reassigned_review = await self.review_queue_service.assign_review(db, review_id, new_reviewer)

            # Add reassignment note
            if reassigned_review.review_notes:
                new_notes = f"REASSIGNED: {reassignment_reason}. {reassigned_review.review_notes}"
            else:
                new_notes = f"REASSIGNED: {reassignment_reason}"

            await self.review_queue_service.update(db, review_id, {"review_notes": new_notes})

            logger.info(f"Reassigned review {review_id} from {review.assigned_to} to {new_reviewer}")
            return reassigned_review

        except Exception as e:
            logger.error(f"Failed to reassign review {review_id}: {e}")
            raise
