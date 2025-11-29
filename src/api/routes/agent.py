"""Agent API routes for BrainForge."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends

from src.models.agent_run import AgentRun, AgentRunCreate, AgentRunStatus
from src.api.dependencies import AgentRunServiceDep, DatabaseSession
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/agent/runs", response_model=AgentRun, status_code=status.HTTP_201_CREATED)
async def execute_agent(
    agent_run_data: AgentRunCreate,
    session: AsyncSession = DatabaseSession,
    agent_run_service = AgentRunServiceDep
):
    """Execute an agent workflow."""
    try:
        # Validate the agent run data using Pydantic model
        validated_data = agent_run_data.model_dump()
        
        # Create the agent run
        agent_run = await agent_run_service.create(session, validated_data)
        return agent_run
    except ValueError as e:
        logger.warning(f"Validation error creating agent run: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid agent run data: {e}"
        )
    except Exception as e:
        logger.error(f"Error creating agent run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute agent workflow"
        )


@router.get("/agent/runs/{run_id}", response_model=AgentRun)
async def get_agent_run(
    run_id: UUID,
    session: AsyncSession = DatabaseSession,
    agent_run_service = AgentRunServiceDep
):
    """Get agent run status."""
    try:
        agent_run = await agent_run_service.get(session, run_id)
        if agent_run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent run not found"
            )
        return agent_run
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving agent run {run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent run status"
        )
