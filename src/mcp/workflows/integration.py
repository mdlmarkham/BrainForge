"""SpiffWorkflow Integration for MCP"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from spiffworkflow_backend import SpiffWorkflow
from spiffworkflow_backend.models.task import Task

from ...models.mcp_workflow import MCPWorkflow
from ...services.database import DatabaseService


class WorkflowOrchestrator:
    """Orchestrates SpiffWorkflow integration for MCP operations"""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        self.workflow_engine = SpiffWorkflow()
        self.active_workflows: dict[UUID, Any] = {}
        self.logger = logging.getLogger(__name__)

    async def start_workflow(self, workflow_id: UUID) -> dict[str, Any]:
        """Start a workflow execution"""

        try:
            # Get workflow definition
            async with self.database_service.session() as session:
                db_workflow = await self.database_service.get_by_id(
                    session, "mcp_workflows", workflow_id
                )

                if not db_workflow:
                    return {
                        "workflow_id": str(workflow_id),
                        "error": "Workflow not found",
                        "status": "failed"
                    }

                workflow = MCPWorkflow.from_orm(db_workflow)

            # Initialize workflow engine
            workflow_instance = self.workflow_engine.create_workflow(
                workflow.bpmn_definition
            )

            # Store active workflow
            self.active_workflows[workflow_id] = {
                "instance": workflow_instance,
                "status": "running",
                "current_step": "initializing"
            }

            # Update workflow status
            await self._update_workflow_status(workflow_id, "running", "initializing", 0.1)

            # Start workflow execution
            asyncio.create_task(self._execute_workflow(workflow_id, workflow_instance))

            return {
                "workflow_id": workflow_id,
                "status": "started",
                "current_step": "initializing",
                "progress": 0.1
            }

        except Exception as e:
            self.logger.error(f"Failed to start workflow: {e}")
            await self._update_workflow_status(workflow_id, "failed", "initialization", 0.0, str(e))
            return {
                "workflow_id": str(workflow_id),
                "error": f"Failed to start workflow: {str(e)}",
                "status": "failed"
            }

    async def _execute_workflow(self, workflow_id: UUID, workflow_instance):
        """Execute workflow asynchronously"""

        try:
            # Execute workflow steps
            while workflow_instance.is_alive():
                # Get current tasks
                ready_tasks = workflow_instance.get_tasks(Task.READY)

                if ready_tasks:
                    current_task = ready_tasks[0]
                    task_name = current_task.task_spec.name

                    # Update status
                    await self._update_workflow_status(
                        workflow_id,
                        "running",
                        task_name,
                        self._calculate_progress(workflow_instance)
                    )

                    # Execute task
                    await self._execute_workflow_task(workflow_id, current_task)

                    # Complete task
                    workflow_instance.complete_task(current_task)

                await asyncio.sleep(0.1)  # Small delay to prevent tight loop

            # Workflow completed
            result = workflow_instance.get_data()
            await self._update_workflow_status(
                workflow_id,
                "completed",
                "completed",
                1.0,
                result=result
            )

            # Clean up
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            await self._update_workflow_status(
                workflow_id,
                "failed",
                "execution",
                self._calculate_progress(workflow_instance),
                str(e)
            )

    async def _execute_workflow_task(self, workflow_id: UUID, task: Task):
        """Execute a specific workflow task"""

        task_name = task.task_spec.name
        self.logger.info(f"Executing workflow task: {task_name}")

        try:
            # Map task names to execution methods
            task_executors = {
                "topic_analysis": self._execute_topic_analysis,
                "source_discovery": self._execute_source_discovery,
                "content_ingestion": self._execute_content_ingestion,
                "semantic_analysis": self._execute_semantic_analysis,
                "connection_mapping": self._execute_connection_mapping,
                "report_generation": self._execute_report_generation,
                "content_parsing": self._execute_content_parsing,
                "semantic_embedding": self._execute_semantic_embedding,
                "quality_assessment": self._execute_quality_assessment,
                "relevance_scoring": self._execute_relevance_scoring,
                "summary_generation": self._execute_summary_generation,
                "note_analysis": self._execute_note_analysis,
                "semantic_comparison": self._execute_semantic_comparison,
                "connection_scoring": self._execute_connection_scoring,
                "link_creation": self._execute_link_creation,
                "visualization_generation": self._execute_visualization_generation
            }

            if task_name in task_executors:
                result = await task_executors[task_name](workflow_id, task)
                task.data = result
            else:
                self.logger.warning(f"Unknown task: {task_name}")
                task.data = {"status": "skipped", "reason": "unknown_task"}

        except Exception as e:
            self.logger.error(f"Task execution failed: {task_name} - {e}")
            task.data = {"status": "failed", "error": str(e)}
            raise

    async def get_workflow_status(self, workflow_id: UUID) -> dict[str, Any]:
        """Get current status of a workflow"""

        if workflow_id not in self.active_workflows:
            # Check database for completed/failed workflows
            async with self.database_service.session() as session:
                db_workflow = await self.database_service.get_by_id(
                    session, "mcp_workflows", workflow_id
                )

                if db_workflow:
                    workflow = MCPWorkflow.from_orm(db_workflow)
                    return {
                        "status": workflow.status,
                        "current_step": "completed" if workflow.status == "completed" else "unknown",
                        "progress": 1.0 if workflow.status == "completed" else 0.0,
                        "result": workflow.result,
                        "error_message": workflow.error_message
                    }
                else:
                    return {
                        "status": "not_found",
                        "current_step": "unknown",
                        "progress": 0.0
                    }

        workflow_info = self.active_workflows[workflow_id]
        workflow_instance = workflow_info["instance"]

        return {
            "status": workflow_info["status"],
            "current_step": workflow_info["current_step"],
            "progress": self._calculate_progress(workflow_instance),
            "result": workflow_instance.get_data() if workflow_instance else None
        }

    async def cancel_workflow(self, workflow_id: UUID) -> dict[str, Any]:
        """Cancel a running workflow"""

        if workflow_id in self.active_workflows:
            workflow_info = self.active_workflows[workflow_id]
            workflow_instance = workflow_info["instance"]

            if workflow_instance and workflow_instance.is_alive():
                workflow_instance.cancel()

            # Update status
            await self._update_workflow_status(workflow_id, "cancelled", "cancelled", 0.0)

            # Clean up
            del self.active_workflows[workflow_id]

            return {
                "workflow_id": str(workflow_id),
                "status": "cancelled",
                "message": "Workflow cancelled successfully"
            }
        else:
            return {
                "workflow_id": str(workflow_id),
                "error": "Workflow not found or not running",
                "status": "failed"
            }

    async def _update_workflow_status(
        self,
        workflow_id: UUID,
        status: str,
        current_step: str,
        progress: float,
        error_message: str = None,
        result: dict[str, Any] = None
    ):
        """Update workflow status in database"""

        try:
            update_data = {
                "status": status,
                "current_step": current_step,
                "progress": progress
            }

            if error_message:
                update_data["error_message"] = error_message

            if result:
                update_data["result"] = result

            async with self.database_service.session() as session:
                await self.database_service.update(
                    session, "mcp_workflows", workflow_id, update_data
                )

        except Exception as e:
            self.logger.error(f"Failed to update workflow status: {e}")

    def _calculate_progress(self, workflow_instance) -> float:
        """Calculate workflow progress percentage"""
        if not workflow_instance:
            return 0.0

        # Simplified progress calculation
        # In a real implementation, this would be more sophisticated
        total_tasks = len(workflow_instance.get_tasks())
        completed_tasks = len([t for t in workflow_instance.get_tasks() if t.state == Task.COMPLETED])

        if total_tasks == 0:
            return 0.0

        return min(completed_tasks / total_tasks, 1.0)

    # Task execution methods (simplified implementations)

    async def _execute_topic_analysis(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        """Execute topic analysis task"""
        await asyncio.sleep(0.5)  # Simulate work
        return {"topics_identified": 3, "analysis_complete": True}

    async def _execute_source_discovery(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        """Execute source discovery task"""
        await asyncio.sleep(0.3)
        return {"sources_found": 5, "discovery_complete": True}

    async def _execute_content_ingestion(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        """Execute content ingestion task"""
        await asyncio.sleep(0.7)
        return {"content_ingested": 10, "ingestion_complete": True}

    async def _execute_semantic_analysis(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        """Execute semantic analysis task"""
        await asyncio.sleep(0.4)
        return {"analysis_performed": True, "semantic_clusters": 2}

    async def _execute_connection_mapping(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        """Execute connection mapping task"""
        await asyncio.sleep(0.6)
        return {"connections_mapped": 8, "mapping_complete": True}

    async def _execute_report_generation(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        """Execute report generation task"""
        await asyncio.sleep(0.8)
        return {"report_generated": True, "report_size": "medium"}

    # Additional task methods would be implemented similarly...
    async def _execute_content_parsing(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.2)
        return {"parsing_complete": True}

    async def _execute_semantic_embedding(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.3)
        return {"embeddings_generated": True}

    async def _execute_quality_assessment(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.4)
        return {"quality_score": 0.85}

    async def _execute_relevance_scoring(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.3)
        return {"relevance_scores_calculated": True}

    async def _execute_summary_generation(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.5)
        return {"summary_generated": True}

    async def _execute_note_analysis(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.3)
        return {"notes_analyzed": 15}

    async def _execute_semantic_comparison(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.4)
        return {"comparisons_made": 25}

    async def _execute_connection_scoring(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.3)
        return {"scores_calculated": True}

    async def _execute_link_creation(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.2)
        return {"links_created": 12}

    async def _execute_visualization_generation(self, workflow_id: UUID, task: Task) -> dict[str, Any]:
        await asyncio.sleep(0.6)
        return {"visualization_created": True}
