"""Integration proposal service for generating and managing content integration recommendations."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.content_source import ContentSource
from ..models.integration_proposal import (
    IntegrationProposal,
    IntegrationProposalCreate,
    ProposalStatus,
)
from ..services.integration.connection_suggester import ConnectionSuggester
from ..services.integration.semantic_analyzer import SemanticAnalyzer
from ..services.integration.tag_suggester import TagSuggester
from ..services.sqlalchemy_service import SQLAlchemyService

logger = logging.getLogger(__name__)


class IntegrationProposalService(SQLAlchemyService[IntegrationProposal]):
    """Service for generating and managing integration proposals."""

    def __init__(self):
        super().__init__(IntegrationProposal)
        self.semantic_analyzer = SemanticAnalyzer()
        self.connection_suggester = ConnectionSuggester()
        self.tag_suggester = TagSuggester()

    async def generate_integration_proposal(self, db: AsyncSession, content_source_id: UUID,
                                          research_run_id: UUID) -> IntegrationProposal:
        """Generate an integration proposal for a content source."""

        try:
            # Check if proposal already exists
            existing_proposal = await self.get_proposal_by_content_source(db, content_source_id)
            if existing_proposal:
                logger.info(f"Integration proposal already exists for content source {content_source_id}")
                return existing_proposal

            # Get content source
            content_source = await self._get_content_source(db, content_source_id)
            if not content_source:
                raise ValueError(f"Content source {content_source_id} not found")

            # Generate integration analysis
            integration_analysis = await self._analyze_integration_potential(db, content_source)

            # Create integration proposal
            proposal_data = IntegrationProposalCreate(
                content_source_id=content_source_id,
                research_run_id=research_run_id,
                proposal_type=integration_analysis["proposal_type"],
                integration_strategy=integration_analysis["integration_strategy"],
                proposed_actions=integration_analysis["proposed_actions"],
                estimated_effort=integration_analysis["estimated_effort"],
                confidence_score=integration_analysis["confidence_score"],
                semantic_similarities=integration_analysis["semantic_similarities"],
                suggested_connections=integration_analysis["suggested_connections"],
                suggested_tags=integration_analysis["suggested_tags"],
                proposal_metadata=integration_analysis["metadata"]
            )

            integration_proposal = await self.create(db, proposal_data)

            logger.info(f"Generated integration proposal {integration_proposal.id} for content source {content_source_id}")
            return integration_proposal

        except Exception as e:
            logger.error(f"Failed to generate integration proposal for content source {content_source_id}: {e}")
            raise

    async def _analyze_integration_potential(self, db: AsyncSession, content_source: ContentSource) -> dict[str, Any]:
        """Analyze the integration potential of a content source."""

        # Perform semantic analysis
        semantic_similarities = await self.semantic_analyzer.analyze_similarity(db, content_source)

        # Suggest connections
        suggested_connections = await self.connection_suggester.suggest_connections(db, content_source)

        # Suggest tags
        suggested_tags = await self.tag_suggester.suggest_tags(db, content_source)

        # Determine integration strategy
        integration_strategy = self._determine_integration_strategy(content_source, semantic_similarities)

        # Generate proposed actions
        proposed_actions = self._generate_proposed_actions(content_source, suggested_connections, suggested_tags)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(semantic_similarities, suggested_connections)

        return {
            "proposal_type": "knowledge_integration",
            "integration_strategy": integration_strategy,
            "proposed_actions": proposed_actions,
            "estimated_effort": self._estimate_effort(content_source, proposed_actions),
            "confidence_score": confidence_score,
            "semantic_similarities": semantic_similarities,
            "suggested_connections": suggested_connections,
            "suggested_tags": suggested_tags,
            "metadata": {
                "content_type": content_source.source_type,
                "analysis_timestamp": self._get_current_timestamp(),
                "similarity_threshold_used": 0.7  # Configurable threshold
            }
        }

    def _determine_integration_strategy(self, content_source: ContentSource,
                                      semantic_similarities: dict[str, Any]) -> str:
        """Determine the appropriate integration strategy."""

        # Base strategy on content type and similarity scores
        if content_source.source_type in ["research_paper", "academic_article"]:
            return "comprehensive_integration"

        # Use similarity scores to refine strategy
        avg_similarity = semantic_similarities.get("average_similarity", 0.5)

        if avg_similarity >= 0.8:
            return "deep_integration"
        elif avg_similarity >= 0.6:
            return "standard_integration"
        else:
            return "basic_integration"

    def _generate_proposed_actions(self, content_source: ContentSource,
                                 suggested_connections: list[dict], suggested_tags: list[str]) -> dict[str, Any]:
        """Generate proposed integration actions."""

        actions = {
            "create_summary": True,
            "extract_key_concepts": True,
            "categorize_content": True,
            "tag_with_suggestions": len(suggested_tags) > 0,
            "establish_connections": len(suggested_connections) > 0,
            "quality_annotation": True
        }

        # Additional actions based on content type
        if content_source.source_type == "research_paper":
            actions["extract_methodology"] = True
            actions["identify_findings"] = True
            actions["map_citations"] = True

        return actions

    def _estimate_effort(self, content_source: ContentSource, proposed_actions: dict[str, Any]) -> str:
        """Estimate the effort required for integration."""

        # Count the number of actions
        action_count = sum(1 for action in proposed_actions.values() if action)

        if action_count <= 3:
            return "low"
        elif action_count <= 6:
            return "medium"
        else:
            return "high"

    def _calculate_confidence_score(self, semantic_similarities: dict[str, Any],
                                 suggested_connections: list[dict]) -> float:
        """Calculate confidence score for integration success."""

        base_confidence = semantic_similarities.get("average_similarity", 0.5)

        # Boost confidence if strong connections are suggested
        strong_connections = [conn for conn in suggested_connections if conn.get("strength", 0) >= 0.7]
        if len(strong_connections) > 0:
            base_confidence += 0.1

        # Cap at 1.0
        return min(1.0, base_confidence)

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for metadata."""

        from datetime import datetime
        return datetime.now().isoformat()

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

    async def get_proposal_by_content_source(self, db: AsyncSession, content_source_id: UUID) -> IntegrationProposal | None:
        """Get integration proposal by content source ID."""

        from sqlalchemy import select

        from ..models.orm.integration_proposal import (
            IntegrationProposal as IntegrationProposalORM,
        )

        result = await db.execute(
            select(IntegrationProposalORM).where(IntegrationProposalORM.content_source_id == content_source_id)
        )
        proposal_orm = result.scalar_one_or_none()

        if proposal_orm:
            return IntegrationProposal.model_validate(proposal_orm)
        return None

    async def get_proposals_for_research_run(self, db: AsyncSession, research_run_id: UUID) -> list[IntegrationProposal]:
        """Get integration proposals for a research run."""

        from sqlalchemy import select

        from ..models.orm.integration_proposal import (
            IntegrationProposal as IntegrationProposalORM,
        )

        result = await db.execute(
            select(IntegrationProposalORM).where(IntegrationProposalORM.research_run_id == research_run_id)
        )
        proposals_orm = result.scalars().all()

        return [IntegrationProposal.model_validate(proposal) for proposal in proposals_orm]

    async def get_proposals_count_for_research_run(self, db: AsyncSession, research_run_id: UUID) -> int:
        """Get count of integration proposals for a research run."""

        from sqlalchemy import func, select

        from ..models.orm.integration_proposal import (
            IntegrationProposal as IntegrationProposalORM,
        )

        query = select(func.count(IntegrationProposalORM.id)).where(
            IntegrationProposalORM.research_run_id == research_run_id
        )

        result = await db.execute(query)
        return result.scalar() or 0

    async def update_proposal_status(self, db: AsyncSession, proposal_id: UUID,
                                   status: ProposalStatus, implementation_notes: str = None) -> IntegrationProposal:
        """Update the status of an integration proposal."""

        try:
            proposal = await self.get(db, proposal_id)
            if not proposal:
                raise ValueError(f"Integration proposal {proposal_id} not found")

            update_data = {"status": status}
            if implementation_notes:
                update_data["implementation_notes"] = implementation_notes

            updated_proposal = await self.update(db, proposal_id, update_data)

            logger.info(f"Updated integration proposal {proposal_id} status to {status}")
            return updated_proposal

        except Exception as e:
            logger.error(f"Failed to update integration proposal {proposal_id} status: {e}")
            raise

    async def get_implemented_proposals(self, db: AsyncSession, research_run_id: UUID = None) -> list[IntegrationProposal]:
        """Get implemented integration proposals."""

        from sqlalchemy import select

        from ..models.orm.integration_proposal import (
            IntegrationProposal as IntegrationProposalORM,
        )

        query = select(IntegrationProposalORM).where(
            IntegrationProposalORM.status == ProposalStatus.IMPLEMENTED
        )

        if research_run_id:
            query = query.where(IntegrationProposalORM.research_run_id == research_run_id)

        query = query.order_by(IntegrationProposalORM.updated_at.desc())

        result = await db.execute(query)
        proposals_orm = result.scalars().all()

        return [IntegrationProposal.model_validate(proposal) for proposal in proposals_orm]

    async def get_proposal_statistics(self, db: AsyncSession, research_run_id: UUID = None) -> dict[str, Any]:
        """Get statistics for integration proposals."""

        from sqlalchemy import func, select

        from ..models.orm.integration_proposal import (
            IntegrationProposal as IntegrationProposalORM,
        )

        base_query = select(IntegrationProposalORM)
        if research_run_id:
            base_query = base_query.where(IntegrationProposalORM.research_run_id == research_run_id)

        # Get counts by status
        status_counts_query = (
            select(
                IntegrationProposalORM.status,
                func.count(IntegrationProposalORM.id).label("count")
            )
            .select_from(base_query)
            .group_by(IntegrationProposalORM.status)
        )

        result = await db.execute(status_counts_query)
        status_counts = result.mappings().all()

        # Get total count
        total_query = select(func.count(IntegrationProposalORM.id)).select_from(base_query)
        total_result = await db.execute(total_query)
        total_count = total_result.scalar() or 0

        # Get average confidence score
        avg_confidence_query = (
            select(func.avg(IntegrationProposalORM.confidence_score).label("avg_confidence"))
            .select_from(base_query)
        )

        avg_confidence_result = await db.execute(avg_confidence_query)
        avg_confidence = avg_confidence_result.scalar() or 0

        return {
            "total_proposals": total_count,
            "status_counts": {row["status"]: row["count"] for row in status_counts},
            "average_confidence_score": round(avg_confidence, 2),
            "research_run_id": str(research_run_id) if research_run_id else None
        }

    async def batch_generate_proposals(self, db: AsyncSession, content_source_ids: list[UUID],
                                     research_run_id: UUID) -> dict[str, Any]:
        """Generate integration proposals for multiple content sources in batch."""

        results = {
            "generated": [],
            "failed": [],
            "total": len(content_source_ids)
        }

        for content_source_id in content_source_ids:
            try:
                proposal = await self.generate_integration_proposal(db, content_source_id, research_run_id)
                results["generated"].append({
                    "content_source_id": str(content_source_id),
                    "proposal_id": str(proposal.id),
                    "confidence_score": proposal.confidence_score
                })
            except Exception as e:
                logger.error(f"Failed to generate proposal for content source {content_source_id}: {e}")
                results["failed"].append({
                    "content_source_id": str(content_source_id),
                    "error": str(e)
                })

        logger.info(f"Batch generated {len(results['generated'])} proposals, {len(results['failed'])} failed")
        return results
