"""Agent API routes for BrainForge."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/agent/runs")
async def execute_agent():
    """Execute an agent workflow."""
    return {"message": "Agent execution endpoint - to be implemented"}


@router.get("/agent/runs/{run_id}")
async def get_agent_run(run_id: str):
    """Get agent run status."""
    return {"message": "Agent run status endpoint - to be implemented"}
