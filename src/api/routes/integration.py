"""Integration proposals API endpoints for managing content integration recommendations."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_db
from ...models.integration_proposal import (
    IntegrationProposal,
    IntegrationProposalCreate,
    ProposalStatus,
)
from ...services.integration.connection_suggester import ConnectionSuggester
from ...services.integration.tag_suggester import TagSuggester
from ...services.integration_proposal_service import IntegrationProposalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integration", tags=["integration"])


@router.post("/proposals", response_model=IntegrationProposal, status_code=status.HTTP_201_CREATED)
async def create_integration_proposal(
    proposal: IntegrationProposalCreate,
    db: AsyncSession = Depends(get_db)
) -> IntegrationProposal:
    """Create a new integration proposal."""

    try:
        proposal_service = IntegrationProposalService()
        return await proposal_service.create(db, proposal)

    except Exception as e:
        logger.error(f"Failed to create integration proposal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create integration proposal: {str(e)}"
        )


@router.post("/proposals/generate", response_model=IntegrationProposal, status_code=status.HTTP_201_CREATED)
async def generate_integration_proposal(
    content_source_id: UUID,
    research_run_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> IntegrationProposal:
    """Generate an integration proposal for a content source."""

    try:
        proposal_service = IntegrationProposalService()
        return await proposal_service.generate_integration_proposal(
            db, content_source_id, research_run_id
        )

    except ValueError as e:
        logger.error(f"Content source not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to generate integration proposal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate integration proposal: {str(e)}"
        )


@router.get("/proposals", response_model=list[IntegrationProposal])
async def get_integration_proposals(
    status: ProposalStatus | None = Query(None, description="Filter by proposal status"),
    content_source_id: UUID | None = Query(None, description="Filter by content source ID"),
    research_run_id: UUID | None = Query(None, description="Filter by research run ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: AsyncSession = Depends(get_db)
) -> list[IntegrationProposal]:
    """Get integration proposals with optional filtering."""

    try:
        proposal_service = IntegrationProposalService()

        if content_source_id:
            # Get proposal by content source
            proposal = await proposal_service.get_proposal_by_content_source(db, content_source_id)
            return [proposal] if proposal else []
        elif research_run_id:
            # Get proposals for research run
            return await proposal_service.get_proposals_for_research_run(db, research_run_id)
        else:
            # Get all proposals with filtering
            proposals = await proposal_service.get_all(db, limit=limit, offset=offset)
            if status:
                proposals = [p for p in proposals if p.status == status]
            return proposals

    except Exception as e:
        logger.error(f"Failed to get integration proposals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration proposals: {str(e)}"
        )


@router.get("/proposals/{proposal_id}", response_model=IntegrationProposal)
async def get_integration_proposal(
    proposal_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> IntegrationProposal:
    """Get a specific integration proposal by ID."""

    try:
        proposal_service = IntegrationProposalService()
        proposal = await proposal_service.get(db, proposal_id)

        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration proposal {proposal_id} not found"
            )

        return proposal

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get integration proposal {proposal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration proposal: {str(e)}"
        )


@router.put("/proposals/{proposal_id}/status", response_model=IntegrationProposal)
async def update_proposal_status(
    proposal_id: UUID,
    status: ProposalStatus,
    implementation_notes: str | None = None,
    db: AsyncSession = Depends(get_db)
) -> IntegrationProposal:
    """Update the status of an integration proposal."""

    try:
        proposal_service = IntegrationProposalService()
        updated_proposal = await proposal_service.update_proposal_status(
            db, proposal_id, status, implementation_notes
        )

        if not updated_proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration proposal {proposal_id} not found"
            )

        return updated_proposal

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update integration proposal {proposal_id} status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update proposal status: {str(e)}"
        )


@router.get("/proposals/{proposal_id}/connections", response_model=dict)
async def get_proposal_connections(
    proposal_id: UUID,
    max_suggestions: int = Query(10, ge=1, le=20, description="Maximum number of connection suggestions"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get connection suggestions for an integration proposal."""

    try:
        proposal_service = IntegrationProposalService()
        connection_suggester = ConnectionSuggester()

        # Get the proposal
        proposal = await proposal_service.get(db, proposal_id)
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration proposal {proposal_id} not found"
            )

        # Get the content source
        content_source = await proposal_service._get_content_source(db, proposal.content_source_id)
        if not content_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content source {proposal.content_source_id} not found"
            )

        # Get connection suggestions
        connections = await connection_suggester.suggest_connections(
            db, content_source, max_suggestions
        )

        # Get connection analysis summary
        connection_analysis = await connection_suggester.get_connection_analysis_summary(
            db, content_source
        )

        return {
            "proposal_id": str(proposal_id),
            "content_source_id": str(proposal.content_source_id),
            "connections": connections,
            "analysis": connection_analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get proposal connections for {proposal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get proposal connections: {str(e)}"
        )


@router.get("/proposals/{proposal_id}/tags", response_model=dict)
async def get_proposal_tags(
    proposal_id: UUID,
    max_tags: int = Query(15, ge=1, le=30, description="Maximum number of tag suggestions"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get tag suggestions for an integration proposal."""

    try:
        proposal_service = IntegrationProposalService()
        tag_suggester = TagSuggester()

        # Get the proposal
        proposal = await proposal_service.get(db, proposal_id)
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Integration proposal {proposal_id} not found"
            )

        # Get the content source
        content_source = await proposal_service._get_content_source(db, proposal.content_source_id)
        if not content_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content source {proposal.content_source_id} not found"
            )

        # Get tag suggestions
        tags = await tag_suggester.suggest_tags(db, content_source, max_tags)

        # Get tag analysis summary
        tag_analysis = await tag_suggester.get_tag_analysis_summary(db, content_source)

        return {
            "proposal_id": str(proposal_id),
            "content_source_id": str(proposal.content_source_id),
            "tags": tags,
            "analysis": tag_analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get proposal tags for {proposal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get proposal tags: {str(e)}"
        )


@router.post("/proposals/batch-generate", response_model=dict)
async def batch_generate_proposals(
    content_source_ids: list[UUID],
    research_run_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Batch generate integration proposals for multiple content sources."""

    try:
        proposal_service = IntegrationProposalService()
        results = await proposal_service.batch_generate_proposals(
            db, content_source_ids, research_run_id
        )

        return results

    except Exception as e:
        logger.error(f"Failed to batch generate integration proposals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch generate proposals: {str(e)}"
        )


@router.get("/proposals/statistics", response_model=dict)
async def get_proposal_statistics(
    research_run_id: UUID | None = Query(None, description="Filter by research run ID"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get integration proposal statistics."""

    try:
        proposal_service = IntegrationProposalService()
        return await proposal_service.get_proposal_statistics(db, research_run_id)

    except Exception as e:
        logger.error(f"Failed to get proposal statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get proposal statistics: {str(e)}"
        )


@router.get("/implemented", response_model=list[IntegrationProposal])
async def get_implemented_proposals(
    research_run_id: UUID | None = Query(None, description="Filter by research run ID"),
    limit: int = Query(20, ge=1, le=50, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: AsyncSession = Depends(get_db)
) -> list[IntegrationProposal]:
    """Get implemented integration proposals."""

    try:
        proposal_service = IntegrationProposalService()
        return await proposal_service.get_implemented_proposals(db, research_run_id)

    except Exception as e:
        logger.error(f"Failed to get implemented proposals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get implemented proposals: {str(e)}"
        )


@router.get("/analysis/{content_source_id}", response_model=dict)
async def get_integration_analysis(
    content_source_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get comprehensive integration analysis for a content source."""

    try:
        proposal_service = IntegrationProposalService()
        connection_suggester = ConnectionSuggester()
        tag_suggester = TagSuggester()

        # Get the content source
        content_source = await proposal_service._get_content_source(db, content_source_id)
        if not content_source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content source {content_source_id} not found"
            )

        # Get connection analysis
        connection_analysis = await connection_suggester.get_connection_analysis_summary(
            db, content_source
        )

        # Get tag analysis
        tag_analysis = await tag_suggester.get_tag_analysis_summary(db, content_source)

        # Check if proposal exists
        existing_proposal = await proposal_service.get_proposal_by_content_source(db, content_source_id)

        return {
            "content_source_id": str(content_source_id),
            "content_source_title": content_source.title,
            "existing_proposal": bool(existing_proposal),
            "connection_analysis": connection_analysis,
            "tag_analysis": tag_analysis,
            "integration_potential": _assess_integration_potential(connection_analysis, tag_analysis)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get integration analysis for content source {content_source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get integration analysis: {str(e)}"
        )


def _assess_integration_potential(connection_analysis: dict, tag_analysis: dict) -> str:
    """Assess the overall integration potential based on analysis results."""

    connection_density = connection_analysis.get("connection_density", "very_low")
    tag_density = tag_analysis.get("tag_density", "very_low")
    avg_connection_strength = connection_analysis.get("average_connection_strength", 0.0)

    if connection_density == "high" and tag_density == "high" and avg_connection_strength >= 0.7:
        return "high"
    elif connection_density in ["medium", "high"] and tag_density in ["medium", "high"]:
        return "medium"
    elif connection_density == "low" and tag_density == "low":
        return "low"
    else:
        return "very_low"
