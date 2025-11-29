"""Review queue API endpoints for managing content review workflows."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.review_queue import ReviewQueue, ReviewQueueCreate, ReviewQueueUpdate, ReviewDecision
from ...models.integration_proposal import IntegrationProposal
from ...services.review_queue_service import ReviewQueueService
from ...services.integration_proposal_service import IntegrationProposalService
from ...services.review_processor import ReviewProcessor
from ...api.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["review"])


@router.post("/queue", response_model=ReviewQueue, status_code=status.HTTP_201_CREATED)
async def create_review_queue(
    review_queue: ReviewQueueCreate,
    db: AsyncSession = Depends(get_db)
) -> ReviewQueue:
    """Create a new review queue entry."""
    
    try:
        review_service = ReviewQueueService()
        return await review_service.create_review_queue(db, review_queue)
        
    except Exception as e:
        logger.error(f"Failed to create review queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review queue: {str(e)}"
        )


@router.get("/queue", response_model=List[ReviewQueue])
async def get_review_queues(
    status: Optional[str] = Query(None, description="Filter by review status"),
    content_source_id: Optional[UUID] = Query(None, description="Filter by content source ID"),
    research_run_id: Optional[UUID] = Query(None, description="Filter by research run ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: AsyncSession = Depends(get_db)
) -> List[ReviewQueue]:
    """Get review queue entries with optional filtering."""
    
    try:
        review_service = ReviewQueueService()
        return await review_service.get_review_queues(
            db, status=status, content_source_id=content_source_id,
            research_run_id=research_run_id, limit=limit, offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to get review queues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review queues: {str(e)}"
        )


@router.get("/queue/{review_queue_id}", response_model=ReviewQueue)
async def get_review_queue(
    review_queue_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ReviewQueue:
    """Get a specific review queue entry by ID."""
    
    try:
        review_service = ReviewQueueService()
        review_queue = await review_service.get_review_queue(db, review_queue_id)
        
        if not review_queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review queue {review_queue_id} not found"
            )
            
        return review_queue
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review queue {review_queue_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review queue: {str(e)}"
        )


@router.put("/queue/{review_queue_id}", response_model=ReviewQueue)
async def update_review_queue(
    review_queue_id: UUID,
    review_update: ReviewQueueUpdate,
    db: AsyncSession = Depends(get_db)
) -> ReviewQueue:
    """Update a review queue entry."""
    
    try:
        review_service = ReviewQueueService()
        updated_queue = await review_service.update_review_queue(db, review_queue_id, review_update)
        
        if not updated_queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review queue {review_queue_id} not found"
            )
            
        return updated_queue
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update review queue {review_queue_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update review queue: {str(e)}"
        )


@router.post("/queue/{review_queue_id}/decide", response_model=ReviewQueue)
async def make_review_decision(
    review_queue_id: UUID,
    decision: ReviewDecision,
    implementation_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> ReviewQueue:
    """Make a decision on a review queue entry."""
    
    try:
        review_processor = ReviewProcessor()
        result = await review_processor.process_review_decision(
            db, review_queue_id, decision, implementation_notes
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review queue {review_queue_id} not found or decision processing failed"
            )
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process review decision for queue {review_queue_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process review decision: {str(e)}"
        )


@router.get("/queue/{review_queue_id}/proposal", response_model=IntegrationProposal)
async def get_review_proposal(
    review_queue_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> IntegrationProposal:
    """Get the integration proposal associated with a review queue entry."""
    
    try:
        review_service = ReviewQueueService()
        proposal_service = IntegrationProposalService()
        
        # Get review queue to find associated proposal
        review_queue = await review_service.get_review_queue(db, review_queue_id)
        if not review_queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review queue {review_queue_id} not found"
            )
        
        # Get the integration proposal
        proposal = await proposal_service.get_proposal_by_content_source(
            db, review_queue.content_source_id
        )
        
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration proposal not found for content source {review_queue.content_source_id}"
            )
            
        return proposal
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get proposal for review queue {review_queue_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review proposal: {str(e)}"
        )


@router.get("/pending", response_model=List[ReviewQueue])
async def get_pending_reviews(
    limit: int = Query(20, ge=1, le=50, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: AsyncSession = Depends(get_db)
) -> List[ReviewQueue]:
    """Get pending review queue entries (awaiting human review)."""
    
    try:
        review_service = ReviewQueueService()
        return await review_service.get_pending_reviews(db, limit=limit, offset=offset)
        
    except Exception as e:
        logger.error(f"Failed to get pending reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending reviews: {str(e)}"
        )


@router.get("/statistics", response_model=dict)
async def get_review_statistics(
    research_run_id: Optional[UUID] = Query(None, description="Filter by research run ID"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get review workflow statistics."""
    
    try:
        review_service = ReviewQueueService()
        return await review_service.get_review_statistics(db, research_run_id)
        
    except Exception as e:
        logger.error(f"Failed to get review statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review statistics: {str(e)}"
        )


@router.post("/batch-process", response_model=dict)
async def batch_process_reviews(
    review_queue_ids: List[UUID],
    decision: ReviewDecision,
    implementation_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Batch process multiple review decisions."""
    
    try:
        review_processor = ReviewProcessor()
        results = await review_processor.batch_process_review_decisions(
            db, review_queue_ids, decision, implementation_notes
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to batch process reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch process reviews: {str(e)}"
        )


@router.get("/workflow/{research_run_id}", response_model=List[ReviewQueue])
async def get_research_run_workflow(
    research_run_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> List[ReviewQueue]:
    """Get the complete review workflow for a research run."""
    
    try:
        review_service = ReviewQueueService()
        return await review_service.get_review_workflow_for_research_run(db, research_run_id)
        
    except Exception as e:
        logger.error(f"Failed to get research run workflow {research_run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get research run workflow: {str(e)}"
        )