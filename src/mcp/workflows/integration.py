"""Real SpiffWorkflow Integration for BrainForge MCP"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from SpiffWorkflow.bpmn import BpmnWorkflow
from SpiffWorkflow.bpmn.parser import BpmnParser
from SpiffWorkflow.bpmn.serializer import BpmnWorkflowSerializer
from SpiffWorkflow import TaskState
from pydantic import BaseModel, Field

from src.services.research_orchestrator import ResearchOrchestrator

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates real SpiffWorkflow execution with constitutional compliance."""
    
    def __init__(self, research_orchestrator: ResearchOrchestrator):
        self.research_orchestrator = research_orchestrator
        self.workflows: Dict[UUID, BpmnWorkflow] = {}
        self.workflow_data: Dict[UUID, Dict[str, Any]] = {}
        self.serializer = BpmnWorkflowSerializer()
        
        # Initialize BPMN parser and load workflow specifications
        self.parser = BpmnParser()
        self._load_workflow_specifications()
    
    def _load_workflow_specifications(self):
        """Load BPMN workflow specifications."""
        try:
            self.parser.add_bpmn_file('src/mcp/workflows/research_workflow.bpmn')
            logger.info("Successfully loaded research workflow BPMN file")
        except Exception as e:
            logger.error(f"Failed to load BPMN workflow specifications: {e}")
            raise
    
    async def create_workflow(self, workflow_type: str, data: Dict[str, Any]) -> UUID:
        """Create a new workflow instance using real SpiffWorkflow."""
        try:
            # Get workflow specification
            if workflow_type == "research_workflow":
                spec = self.parser.get_spec('ResearchWorkflow')
                subprocess_specs = self.parser.get_subprocess_specs('ResearchWorkflow')
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            # Create workflow instance
            workflow = BpmnWorkflow(spec, subprocess_specs)
            workflow_id = uuid4()
            
            # Set initial data with constitutional compliance
            workflow_data = data.copy()
            workflow_data["constitutional_audit"] = {
                "workflow_created": True,
                "workflow_type": workflow_type,
                "workflow_id": str(workflow_id)
            }
            workflow.data.update(workflow_data)
            
            # Store workflow and its data
            self.workflows[workflow_id] = workflow
            self.workflow_data[workflow_id] = workflow_data
            
            logger.info(f"Created workflow {workflow_id} of type {workflow_type}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: UUID) -> Dict[str, Any]:
        """Get workflow status using real SpiffWorkflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        # Get all tasks
        all_tasks = workflow.get_tasks()
        ready_tasks = workflow.get_tasks(state=TaskState.READY)
        completed_tasks = workflow.get_tasks(state=TaskState.COMPLETED)
        
        return {
            "workflow_id": workflow_id,
            "is_completed": workflow.is_completed(),
            "is_alive": not workflow.is_completed(),
            "total_tasks": len(all_tasks),
            "completed_tasks": len(completed_tasks),
            "ready_tasks": len(ready_tasks),
            "ready_task_details": [
                {
                    "task_id": task.id,
                    "task_name": task.task_spec.name,
                    "description": getattr(task.task_spec, 'description', '')
                }
                for task in ready_tasks
            ],
            "data": workflow.data
        }
    
    async def execute_workflow_step(self, workflow_id: UUID) -> Dict[str, Any]:
        """Execute the next workflow step using real SpiffWorkflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        try:
            # Execute automated engine steps
            workflow.do_engine_steps()
            
            # Get ready manual tasks
            ready_tasks = workflow.get_tasks(state=TaskState.READY, manual=True)
            
            if ready_tasks:
                # For now, auto-complete the first ready task with mock data
                # In a real implementation, this would wait for user input
                task = ready_tasks[0]
                task_result = await self._execute_task_logic(task.task_spec.name, workflow.data)
                
                # Update task data and complete it
                task.data.update(task_result)
                task.run()
                
                # Continue with engine steps
                workflow.do_engine_steps()
            
            return await self.get_workflow_status(workflow_id)
            
        except Exception as e:
            logger.error(f"Failed to execute workflow step: {e}")
            raise
    
    async def complete_task(self, workflow_id: UUID, task_id: int, task_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Complete a specific task in the workflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        task_data = task_data or {}
        
        try:
            # Find the task by ID
            task = None
            for t in workflow.get_tasks():
                if t.id == task_id:
                    task = t
                    break
            
            if not task:
                raise ValueError(f"Task {task_id} not found in workflow {workflow_id}")
            
            if task.state != TaskState.READY:
                raise ValueError(f"Task {task_id} is not in READY state")
            
            # Execute task logic and update data
            task_result = await self._execute_task_logic(task.task_spec.name, {**workflow.data, **task_data})
            task.data.update(task_result)
            
            # Complete the task
            task.run()
            
            # Continue with engine steps
            workflow.do_engine_steps()
            
            return {
                "task_completed": task.task_spec.name,
                "result": task_result,
                "workflow_status": await self.get_workflow_status(workflow_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to complete task: {e}")
            raise
    
    async def _execute_task_logic(self, task_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific task logic with constitutional compliance."""
        constitutional_audit = data.get("constitutional_audit", {})
        
        if task_name == "Topic Analysis":
            result = await self._topic_analysis(data)
        elif task_name == "Source Discovery":
            result = await self._source_discovery(data)
        elif task_name == "Content Analysis":
            result = await self._content_analysis(data)
        elif task_name == "Synthesis":
            result = await self._synthesis(data)
        elif task_name == "Report Generation":
            result = await self._report_generation(data)
        else:
            result = {"status": "unknown_task", "data": data}
        
        # Update constitutional audit
        constitutional_audit[f"{task_name.lower().replace(' ', '_')}_completed"] = True
        result["constitutional_audit"] = constitutional_audit
        
        return result
    
    async def _topic_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute topic analysis task."""
        topic = data.get("topic", "")
        return {
            "task": "topic_analysis",
            "topic": topic,
            "analysis": f"Analyzed topic: {topic}",
            "scope_defined": True
        }
    
    async def _source_discovery(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute source discovery task."""
        topic = data.get("topic", "")
        max_sources = data.get("max_sources", 10)
        
        sources = await self.research_orchestrator.gather_sources(topic, max_sources)
        
        return {
            "task": "source_discovery",
            "topic": topic,
            "sources_found": len(sources),
            "sources": sources
        }
    
    async def _content_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content analysis task."""
        sources = data.get("sources", [])
        
        analysis = await self.research_orchestrator.analyze_content(sources)
        
        return {
            "task": "content_analysis",
            "sources_analyzed": len(sources),
            "analysis": analysis
        }
    
    async def _synthesis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute synthesis task."""
        analysis = data.get("analysis", {})
        
        synthesis = await self.research_orchestrator.synthesize_findings(analysis)
        
        return {
            "task": "synthesis",
            "synthesis": synthesis,
            "insights_generated": True
        }
    
    async def _report_generation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation task."""
        synthesis = data.get("synthesis", {})
        
        report = await self.research_orchestrator.generate_report(synthesis)
        
        return {
            "task": "report_generation",
            "report": report,
            "report_generated": True
        }
    
    async def serialize_workflow(self, workflow_id: UUID) -> str:
        """Serialize workflow state for persistence."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        workflow_dict = self.serializer.to_dict(workflow)
        return json.dumps(workflow_dict, indent=2)
    
    async def deserialize_workflow(self, workflow_id: UUID, serialized_state: str) -> None:
        """Deserialize workflow state from persistence."""
        workflow_dict = json.loads(serialized_state)
        workflow = self.serializer.from_dict(workflow_dict)
        self.workflows[workflow_id] = workflow
    
    async def cancel_workflow(self, workflow_id: UUID) -> Dict[str, Any]:
        """Cancel a workflow."""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Remove workflow from active workflows
        del self.workflows[workflow_id]
        if workflow_id in self.workflow_data:
            del self.workflow_data[workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "cancelled": True,
            "constitutional_audit": {"workflow_cancelled": True}
        }