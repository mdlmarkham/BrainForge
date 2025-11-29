"""MCP Workflow Tools"""

import logging
import json
from typing import Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ...models.mcp_workflow import MCPWorkflowCreate, MCPWorkflow
from ...services.database import DatabaseService
from .workflows.integration import WorkflowOrchestrator


class WorkflowStartRequest(BaseModel):
    """Workflow start request"""
    workflow_type: str = Field(..., description="Type of workflow to start")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters")
    priority: str = Field("normal", description="Workflow priority")


class WorkflowStatus(BaseModel):
    """Workflow status response"""
    workflow_id: UUID
    workflow_type: str
    status: str
    current_step: str
    progress: float
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class WorkflowTools:
    """Workflow management tools for BrainForge library"""
    
    def __init__(self, database_service: DatabaseService, workflow_orchestrator: WorkflowOrchestrator):
        self.database_service = database_service
        self.workflow_orchestrator = workflow_orchestrator
        self.logger = logging.getLogger(__name__)
    
    async def start_research_workflow(
        self, 
        workflow_type: str, 
        parameters: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Start a research workflow for agent operations"""
        
        try:
            # Validate workflow type
            supported_workflows = ["research_discovery", "content_analysis", "connection_mapping"]
            if workflow_type not in supported_workflows:
                return {
                    "error": f"Unsupported workflow type. Supported: {supported_workflows}",
                    "status": "failed"
                }
            
            # Create workflow record
            workflow_create = MCPWorkflowCreate(
                workflow_type=workflow_type,
                bpmn_definition=self._get_bpmn_template(workflow_type),
                parameters=parameters or {},
                status="initializing",
                priority=priority
            )
            
            async with self.database_service.session() as session:
                db_workflow = await self.database_service.create(
                    session, "mcp_workflows", workflow_create.dict()
                )
                workflow = MCPWorkflow.from_orm(db_workflow)
            
            # Start the workflow
            workflow_result = await self.workflow_orchestrator.start_workflow(workflow.id)
            
            return {
                "workflow_id": workflow.id,
                "workflow_type": workflow_type,
                "status": workflow_result.get("status", "started"),
                "current_step": workflow_result.get("current_step", "initializing"),
                "progress": workflow_result.get("progress", 0.0),
                "parameters": parameters or {},
                "priority": priority
            }
            
        except Exception as e:
            self.logger.error(f"Workflow start failed: {e}")
            return {
                "workflow_type": workflow_type,
                "error": f"Failed to start workflow: {str(e)}",
                "status": "failed"
            }
    
    async def get_workflow_status(self, workflow_id: UUID) -> Dict[str, Any]:
        """Get the status of a running workflow"""
        
        try:
            # Get workflow record
            async with self.database_service.session() as session:
                db_workflow = await self.database_service.get_by_id(
                    session, "mcp_workflows", workflow_id
                )
                
                if not db_workflow:
                    return {
                        "workflow_id": str(workflow_id),
                        "error": "Workflow not found",
                        "status": "not_found"
                    }
                
                workflow = MCPWorkflow.from_orm(db_workflow)
            
            # Get current status from orchestrator
            status_info = await self.workflow_orchestrator.get_workflow_status(workflow_id)
            
            return {
                "workflow_id": workflow_id,
                "workflow_type": workflow.workflow_type,
                "status": status_info.get("status", workflow.status),
                "current_step": status_info.get("current_step", "unknown"),
                "progress": status_info.get("progress", 0.0),
                "result": status_info.get("result"),
                "error_message": status_info.get("error_message"),
                "created_at": workflow.created_at.isoformat() if workflow.created_at else "Unknown",
                "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else "Unknown"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get workflow status: {e}")
            return {
                "workflow_id": str(workflow_id),
                "error": f"Failed to get workflow status: {str(e)}",
                "status": "error"
            }
    
    async def list_workflows(
        self, 
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List workflows with optional filtering"""
        
        try:
            filters = {}
            if status:
                filters["status"] = status
            if workflow_type:
                filters["workflow_type"] = workflow_type
            
            async with self.database_service.session() as session:
                db_workflows = await self.database_service.get_all(
                    session, 
                    "mcp_workflows", 
                    filters=filters,
                    limit=limit,
                    order_by="created_at DESC"
                )
                
                workflows = []
                for db_workflow in db_workflows:
                    workflow = MCPWorkflow.from_orm(db_workflow)
                    workflows.append({
                        "workflow_id": workflow.id,
                        "workflow_type": workflow.workflow_type,
                        "status": workflow.status,
                        "priority": workflow.priority,
                        "created_at": workflow.created_at.isoformat() if workflow.created_at else "Unknown",
                        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else "Unknown"
                    })
                
                return {
                    "total_workflows": len(workflows),
                    "workflows": workflows,
                    "filters": {
                        "status": status,
                        "workflow_type": workflow_type
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to list workflows: {e}")
            return {
                "error": f"Failed to list workflows: {str(e)}",
                "status": "failed"
            }
    
    async def cancel_workflow(self, workflow_id: UUID) -> Dict[str, Any]:
        """Cancel a running workflow"""
        
        try:
            result = await self.workflow_orchestrator.cancel_workflow(workflow_id)
            
            # Update workflow status
            async with self.database_service.session() as session:
                await self.database_service.update(
                    session, 
                    "mcp_workflows", 
                    workflow_id, 
                    {"status": "cancelled"}
                )
            
            return {
                "workflow_id": str(workflow_id),
                "status": "cancelled",
                "message": result.get("message", "Workflow cancelled")
            }
            
        except Exception as e:
            self.logger.error(f"Failed to cancel workflow: {e}")
            return {
                "workflow_id": str(workflow_id),
                "error": f"Failed to cancel workflow: {str(e)}",
                "status": "failed"
            }
    
    def _get_bpmn_template(self, workflow_type: str) -> Dict[str, Any]:
        """Get BPMN template for workflow type"""
        
        templates = {
            "research_discovery": {
                "process_id": "research_discovery",
                "name": "Research Discovery Workflow",
                "steps": [
                    "topic_analysis",
                    "source_discovery", 
                    "content_ingestion",
                    "semantic_analysis",
                    "connection_mapping",
                    "report_generation"
                ]
            },
            "content_analysis": {
                "process_id": "content_analysis",
                "name": "Content Analysis Workflow",
                "steps": [
                    "content_parsing",
                    "semantic_embedding",
                    "quality_assessment",
                    "relevance_scoring",
                    "summary_generation"
                ]
            },
            "connection_mapping": {
                "process_id": "connection_mapping",
                "name": "Connection Mapping Workflow",
                "steps": [
                    "note_analysis",
                    "semantic_comparison",
                    "connection_scoring",
                    "link_creation",
                    "visualization_generation"
                ]
            }
        }
        
        return templates.get(workflow_type, {})