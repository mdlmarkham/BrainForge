"""Quality assessment service for evaluating content credibility and relevance."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.content_source import ContentSource
from ..models.quality_assessment import (
    QualityAssessment,
    QualityAssessmentCreate,
)
from ..services.ai.classifier import ContentClassifier
from ..services.ai.quality_rationale import QualityRationaleGenerator
from ..services.ai.summarizer import ContentSummarizer
from ..services.scoring.completeness_scorer import CompletenessScorer
from ..services.scoring.credibility_scorer import CredibilityScorer
from ..services.scoring.freshness_scorer import FreshnessScorer
from ..services.scoring.relevance_scorer import RelevanceScorer

logger = logging.getLogger(__name__)


class QualityAssessmentService:
    """Service for assessing content quality and generating quality scores."""

    def __init__(self):
        self.credibility_scorer = CredibilityScorer()
        self.relevance_scorer = RelevanceScorer()
        self.freshness_scorer = FreshnessScorer()
        self.completeness_scorer = CompletenessScorer()
        self.summarizer = ContentSummarizer()
        self.classifier = ContentClassifier()
        self.rationale_generator = QualityRationaleGenerator()

    async def assess_content_quality(self, db: AsyncSession, content_source_id: UUID) -> QualityAssessment:
        """Assess the quality of a content source and generate quality scores."""

        try:
            # Get the content source
            content_source = await self._get_content_source(db, content_source_id)
            if not content_source:
                raise ValueError(f"Content source {content_source_id} not found")

            logger.info(f"Assessing quality for content source {content_source_id}")

            # Generate individual scores
            credibility_score = await self.credibility_scorer.score_content(content_source)
            relevance_score = await self.relevance_scorer.score_content(content_source)
            freshness_score = await self.freshness_scorer.score_content(content_source)
            completeness_score = await self.completeness_scorer.score_content(content_source)

            # Calculate weighted overall score
            overall_score = self._calculate_weighted_score(
                credibility_score, relevance_score, freshness_score, completeness_score
            )

            # Generate AI-powered summaries and classifications
            summary = await self.summarizer.summarize_content(content_source)
            classification = await self.classifier.classify_content(content_source)
            rationale = await self.rationale_generator.generate_rationale(
                content_source, credibility_score, relevance_score, freshness_score, completeness_score
            )

            # Create quality assessment
            quality_assessment_data = QualityAssessmentCreate(
                content_source_id=content_source_id,
                credibility_score=credibility_score,
                relevance_score=relevance_score,
                freshness_score=freshness_score,
                completeness_score=completeness_score,
                overall_score=overall_score,
                summary=summary,
                classification=classification,
                rationale=rationale,
                assessment_metadata={
                    "scoring_weights": {
                        "credibility": 0.4,
                        "relevance": 0.3,
                        "freshness": 0.2,
                        "completeness": 0.1
                    },
                    "assessment_method": "ai_enhanced"
                }
            )

            # For now, return the assessment data without database persistence
            # This is a temporary fix until ORM models are implemented
            quality_assessment = QualityAssessment(
                id=UUID(int=0),  # Temporary ID
                **quality_assessment_data.model_dump()
            )

            logger.info(f"Quality assessment completed for content source {content_source_id}")
            return quality_assessment

        except Exception as e:
            logger.error(f"Failed to assess quality for content source {content_source_id}: {e}")
            raise

    def _calculate_weighted_score(self, credibility: float, relevance: float,
                                 freshness: float, completeness: float) -> float:
        """Calculate weighted overall score based on predefined weights."""

        weights = {
            "credibility": 0.4,  # Most important - content trustworthiness
            "relevance": 0.3,    # Important - topic alignment
            "freshness": 0.2,    # Moderate - timeliness
            "completeness": 0.1  # Least important - content depth
        }

        weighted_score = (
            credibility * weights["credibility"] +
            relevance * weights["relevance"] +
            freshness * weights["freshness"] +
            completeness * weights["completeness"]
        )

        return round(weighted_score, 2)

    async def _get_content_source(self, db: AsyncSession, content_source_id: UUID) -> ContentSource | None:
        """Get content source by ID."""
        # Temporary implementation - return a mock content source
        # This will be properly implemented when ORM models are available
        return ContentSource(
            id=content_source_id,
            title="Mock Content Source",
            url="https://example.com",
            content_type="article",
            content="Mock content for quality assessment",
            metadata={}
        )

    async def get_quality_assessment_for_source(self, db: AsyncSession, content_source_id: UUID) -> QualityAssessment | None:
        """Get quality assessment for a specific content source."""
        # Temporary implementation - return None for now
        # This will be properly implemented when ORM models are available
        return None

    async def get_approved_sources_for_research_run(self, db: AsyncSession, research_run_id: UUID,
                                                   min_score: float = 0.7) -> list[ContentSource]:
        """Get content sources that passed quality assessment for a research run."""
        # Temporary implementation - return empty list for now
        # This will be properly implemented when ORM models are available
        return []

    async def get_assessed_sources_count_for_research_run(self, db: AsyncSession, research_run_id: UUID) -> int:
        """Get count of assessed content sources for a research run."""
        # Temporary implementation - return 0 for now
        # This will be properly implemented when ORM models are available
        return 0

    async def get_quality_statistics(self, db: AsyncSession, research_run_id: UUID) -> dict[str, Any]:
        """Get quality statistics for a research run."""

        from sqlalchemy import func, join, select

        from ..models.orm.content_source import ContentSource as ContentSourceORM
        from ..models.orm.quality_assessment import (
            QualityAssessment as QualityAssessmentORM,
        )

        # Get basic statistics
        stats_query = (
            select(
                func.count(QualityAssessmentORM.id).label("total_assessments"),
                func.avg(QualityAssessmentORM.overall_score).label("avg_score"),
                func.min(QualityAssessmentORM.overall_score).label("min_score"),
                func.max(QualityAssessmentORM.overall_score).label("max_score"),
                func.avg(QualityAssessmentORM.credibility_score).label("avg_credibility"),
                func.avg(QualityAssessmentORM.relevance_score).label("avg_relevance"),
                func.avg(QualityAssessmentORM.freshness_score).label("avg_freshness"),
                func.avg(QualityAssessmentORM.completeness_score).label("avg_completeness")
            )
            .select_from(
                join(ContentSourceORM, QualityAssessmentORM,
                     ContentSourceORM.id == QualityAssessmentORM.content_source_id)
            )
            .where(ContentSourceORM.research_run_id == research_run_id)
        )

        result = await db.execute(stats_query)
        stats = result.mappings().one()

        # Get score distribution
        distribution_query = (
            select(
                QualityAssessmentORM.overall_score,
                func.count(QualityAssessmentORM.id).label("count")
            )
            .select_from(
                join(ContentSourceORM, QualityAssessmentORM,
                     ContentSourceORM.id == QualityAssessmentORM.content_source_id)
            )
            .where(ContentSourceORM.research_run_id == research_run_id)
            .group_by(QualityAssessmentORM.overall_score)
            .order_by(QualityAssessmentORM.overall_score)
        )

        distribution_result = await db.execute(distribution_query)
        distribution = distribution_result.mappings().all()

        return {
            "total_assessments": stats["total_assessments"] or 0,
            "average_score": round(stats["avg_score"] or 0, 2),
            "min_score": stats["min_score"] or 0,
            "max_score": stats["max_score"] or 0,
            "average_credibility": round(stats["avg_credibility"] or 0, 2),
            "average_relevance": round(stats["avg_relevance"] or 0, 2),
            "average_freshness": round(stats["avg_freshness"] or 0, 2),
            "average_completeness": round(stats["avg_completeness"] or 0, 2),
            "score_distribution": [
                {"score": dist["overall_score"], "count": dist["count"]}
                for dist in distribution
            ]
        }

    async def reassess_content_quality(self, db: AsyncSession, content_source_id: UUID) -> QualityAssessment:
        """Reassess the quality of a content source with updated scoring."""
        # Simply create a new assessment (no deletion needed in temporary implementation)
        return await self.assess_content_quality(db, content_source_id)

    async def get_high_quality_sources(self, db: AsyncSession, min_score: float = 0.8,
                                      limit: int = 10) -> list[ContentSource]:
        """Get high-quality content sources across all research runs."""

        from sqlalchemy import join, select

        from ..models.orm.content_source import ContentSource as ContentSourceORM
        from ..models.orm.quality_assessment import (
            QualityAssessment as QualityAssessmentORM,
        )

        query = (
            select(ContentSourceORM)
            .select_from(
                join(ContentSourceORM, QualityAssessmentORM,
                     ContentSourceORM.id == QualityAssessmentORM.content_source_id)
            )
            .where(QualityAssessmentORM.overall_score >= min_score)
            .order_by(QualityAssessmentORM.overall_score.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        sources_orm = result.scalars().all()

        return [ContentSource.model_validate(source) for source in sources_orm]
