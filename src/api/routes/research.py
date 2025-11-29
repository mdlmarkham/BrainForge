"""Research API endpoints for automated content discovery and evaluation."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.research_run import ResearchRun, ResearchRunCreate, ResearchRunUpdate
from ...models.content_source import ContentSource
from ...services.research_run_service import ResearchRunService
from ...services.content_discovery_service import ContentDiscoveryService
from ...api.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/runs", response_model=ResearchRun, status_code=status.HTTP_201_CREATED)
async def create_research_run(
    research_run_create: ResearchRunCreate,
    db: AsyncSession = Depends(get_db)
) -> ResearchRun:
    """Create a new research run for automated content discovery."""
    
    try:
        research_run_service = ResearchRunService()
        research_run = await research_run_service.create_research_run(
            db,
            research_run_create.research_topic,
            research_run_create.created_by,
            research_run_create.research_parameters
        )
        
        logger.info(f"Created research run {research_run.id}")
        return research_run
        
    except Exception as e:
        logger.error(f"Failed to create research run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create research run: {str(e)}"
        )


@router.get("/runs/{research_run_id}", response_model=ResearchRun)
async def get_research_run(
    research_run_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ResearchRun:
    """Get a specific research run by ID."""
    
    try:
        research_run_service = ResearchRunService()
        research_run = await research_run_service.get(db, research_run_id)
        
        if not research_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research run {research_run_id} not found"
            )
        
        return research_run
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get research run {research_run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get research run: {str(e)}"
        )


@router.get("/runs", response_model=List[ResearchRun])
async def list_research_runs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[ResearchRun]:
    """List research runs with pagination."""
    
    try:
        research_run_service = ResearchRunService()
        research_runs = await research_run_service.list(db, skip, limit)
        
        return research_runs
        
    except Exception as e:
        logger.error(f"Failed to list research runs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list research runs: {str(e)}"
        )


@router.post("/runs/{research_run_id}/start", response_model=ResearchRun)
async def start_research_run(
    research_run_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ResearchRun:
    """Start a research run to begin content discovery."""
    
    try:
        research_run_service = ResearchRunService()
        research_run = await research_run_service.start_research_run(db, research_run_id)
        
        if not research_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research run {research_run_id} not found"
            )
        
        # Start content discovery in background
        content_discovery_service = ContentDiscoveryService()
        
        # This would typically be handled by a background task or queue
        # For now, we'll just log the intent
        logger.info(f"Research run {research_run_id} started - content discovery should begin")
        
        return research_run
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start research run {research_run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start research run: {str(e)}"
        )


@router.get("/runs/{research_run_id}/sources", response_model=List[ContentSource])
async def get_research_run_sources(
    research_run_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> List[ContentSource]:
    """Get content sources discovered by a research run."""
    
    try:
        content_discovery_service = ContentDiscoveryService()
        sources = await content_discovery_service.get_content_sources_for_research_run(db, research_run_id)
        
        return sources
        
    except Exception as e:
        logger.error(f"Failed to get sources for research run {research_run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get research run sources: {str(e)}"
        )


@router.get("/runs/pending", response_model=List[ResearchRun])
async def get_pending_research_runs(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
) -> List[ResearchRun]:
    """Get pending research runs that need to be processed."""
    
    try:
        research_run_service = ResearchRunService()
        pending_runs = await research_run_service.get_pending_runs(db, limit)
        
        return pending_runs
        
    except Exception as e:
        logger.error(f"Failed to get pending research runs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending research runs: {str(e)}"
        )


@router.get("/runs/running", response_model=List[ResearchRun])
async def get_running_research_runs(
    db: AsyncSession = Depends(get_db)
) -> List[ResearchRun]:
    """Get currently running research runs."""
    
    try:
        research_run_service = ResearchRunService()
        running_runs = await research_run_service.get_running_runs(db)
        
        return running_runs
        
    except Exception as e:
        logger.error(f"Failed to get running research runs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get running research runs: {str(e)}"
        )


@router.put("/runs/{research_run_id}", response_model=ResearchRun)
async def update_research_run(
    research_run_id: UUID,
    research_run_update: ResearchRunUpdate,
    db: AsyncSession = Depends(get_db)
) -> ResearchRun:
    """Update a research run."""
    
    try:
        research_run_service = ResearchRunService()
        research_run = await research_run_service.update(
            db, research_run_id, research_run_update.model_dump(exclude_unset=True)
        )
        
        if not research_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Research run {research_run_id} not found"
            )
        
        return research_run
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update research run {research_run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update research run: {str(e)}"
        )