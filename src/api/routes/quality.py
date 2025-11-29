"""Quality assessment API endpoints for content evaluation and scoring."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.quality_assessment import QualityAssessment, QualityAssessmentCreate
from ...models.content_source import ContentSource
from ...services.quality_assessment_service import QualityAssessmentService
from ...services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality", tags=["quality"])


@router.post("/assessments", response_model=QualityAssessment, status_code=status.HTTP_201_CREATED)
async def create_quality_assessment(
    quality_assessment_create: QualityAssessmentCreate,
    db: AsyncSession = Depends(get_db)
) -> QualityAssessment:
    """Create a new quality assessment for a content source."""
    
    try:
        quality_service = QualityAssessmentService()
        quality_assessment = await quality_service.create(db, quality_assessment_create)
        
        logger.info(f"Created quality assessment {quality_assessment.id}")
        return quality_assessment
        
    except Exception as e:
        logger.error(f"Failed to create quality assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create quality assessment: {str(e)}"
        )


@router.post("/sources/{content_source_id}/assess", response_model=QualityAssessment)
async def assess_content_quality(
    content_source_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> QualityAssessment:
    """Assess the quality of a content source and generate quality scores."""
    
    try:
        quality_service = QualityAssessmentService()
        quality_assessment = await quality_service.assess_content_quality(db, content_source_id)
        
        logger.info(f"Assessed quality for content source {content_source_id}")
        return quality_assessment
        
    except ValueError as e:
        logger.error(f"Content source not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content source {content_source_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to assess content quality for {content_source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess content quality: {str(e)}"
        )


@router.get("/sources/{content_source_id}/assessment", response_model=Optional[QualityAssessment])
async def get_quality_assessment_for_source(
    content_source_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Optional[QualityAssessment]:
    """Get the quality assessment for a specific content source."""
    
    try:
        quality_service = QualityAssessmentService()
        quality_assessment = await quality_service.get_quality_assessment_for_source(db, content_source_id)
        
        return quality_assessment
        
    except Exception as e:
        logger.error(f"Failed to get quality assessment for content source {content_source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality assessment: {str(e)}"
        )


@router.get("/research-runs/{research_run_id}/approved-sources", response_model=List[ContentSource])
async def get_approved_sources_for_research_run(
    research_run_id: UUID,
    min_score: float = 0.7,
    db: AsyncSession = Depends(get_db)
) -> List[ContentSource]:
    """Get content sources that passed quality assessment for a research run."""
    
    try:
        quality_service = QualityAssessmentService()
        approved_sources = await quality_service.get_approved_sources_for_research_run(
            db, research_run_id, min_score
        )
        
        logger.info(f"Retrieved {len(approved_sources)} approved sources for research run {research_run_id}")
        return approved_sources
        
    except Exception as e:
        logger.error(f"Failed to get approved sources for research run {research_run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approved sources: {str(e)}"
        )


@router.get("/research-runs/{research_run_id}/statistics", response_model=dict)
async def get_quality_statistics(
    research_run_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get quality statistics for a research run."""
    
    try:
        quality_service = QualityAssessmentService()
        statistics = await quality_service.get_quality_statistics(db, research_run_id)
        
        return statistics
        
    except Exception as e:
        logger.error(f"Failed to get quality statistics for research run {research_run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality statistics: {str(e)}"
        )


@router.post("/sources/{content_source_id}/reassess", response_model=QualityAssessment)
async def reassess_content_quality(
    content_source_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> QualityAssessment:
    """Reassess the quality of a content source with updated scoring."""
    
    try:
        quality_service = QualityAssessmentService()
        quality_assessment = await quality_service.reassess_content_quality(db, content_source_id)
        
        logger.info(f"Reassessed quality for content source {content_source_id}")
        return quality_assessment
        
    except ValueError as e:
        logger.error(f"Content source not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content source {content_source_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to reassess content quality for {content_source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reassess content quality: {str(e)}"
        )


@router.get("/high-quality-sources", response_model=List[ContentSource])
async def get_high_quality_sources(
    min_score: float = 0.8,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
) -> List[ContentSource]:
    """Get high-quality content sources across all research runs."""
    
    try:
        quality_service = QualityAssessmentService()
        high_quality_sources = await quality_service.get_high_quality_sources(db, min_score, limit)
        
        logger.info(f"Retrieved {len(high_quality_sources)} high-quality sources")
        return high_quality_sources
        
    except Exception as e:
        logger.error(f"Failed to get high-quality sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get high-quality sources: {str(e)}"
        )


@router.get("/assessments/{assessment_id}", response_model=QualityAssessment)
async def get_quality_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> QualityAssessment:
    """Get a specific quality assessment by ID."""
    
    try:
        quality_service = QualityAssessmentService()
        quality_assessment = await quality_service.get(db, assessment_id)
        
        if not quality_assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quality assessment {assessment_id} not found"
            )
        
        return quality_assessment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality assessment: {str(e)}"
        )


@router.get("/assessments", response_model=List[QualityAssessment])
async def list_quality_assessments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[QualityAssessment]:
    """List quality assessments with pagination."""
    
    try:
        quality_service = QualityAssessmentService()
        assessments = await quality_service.list(db, skip, limit)
        
        return assessments
        
    except Exception as e:
        logger.error(f"Failed to list quality assessments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list quality assessments: {str(e)}"
        )


@router.delete("/assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quality_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a quality assessment."""
    
    try:
        quality_service = QualityAssessmentService()
        success = await quality_service.delete(db, assessment_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quality assessment {assessment_id} not found"
            )
        
        logger.info(f"Deleted quality assessment {assessment_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete quality assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete quality assessment: {str(e)}"
        )


@router.get("/breakdown/{content_source_id}", response_model=dict)
async def get_quality_breakdown(
    content_source_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get detailed quality scoring breakdown for a content source."""
    
    try:
        # This would typically call a method that provides detailed breakdown
        # For now, we'll get the assessment and return its details
        quality_service = QualityAssessmentService()
        assessment = await quality_service.get_quality_assessment_for_source(db, content_source_id)
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No quality assessment found for content source {content_source_id}"
            )
        
        breakdown = {
            "content_source_id": str(content_source_id),
            "overall_score": assessment.overall_score,
            "dimension_scores": {
                "credibility": assessment.credibility_score,
                "relevance": assessment.relevance_score,
                "freshness": assessment.freshness_score,
                "completeness": assessment.completeness_score
            },
            "summary": assessment.summary,
            "classification": assessment.classification,
            "rationale": assessment.rationale,
            "assessment_date": assessment.created_at.isoformat() if assessment.created_at else None
        }
        
        return breakdown
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality breakdown for content source {content_source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality breakdown: {str(e)}"
        )