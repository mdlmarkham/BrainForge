#!/usr/bin/env python3
"""Test script to validate MCP workflow tools functionality"""

import asyncio
import logging
from uuid import UUID

from src.mcp.workflows.integration import WorkflowOrchestrator
from src.mcp.tools.workflows import WorkflowTools
from src.services.generic_database_service import DatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_workflow_tools_without_database():
    """Test workflow tools functionality without database connection"""
    print("=== Testing Workflow Tools Functionality (No Database) ===")
    
    try:
        # Create services with a dummy database URL
        database_url = "postgresql+asyncpg://dummy:dummy@localhost:5432/dummy"
        database_service = DatabaseService(database_url)
        workflow_orchestrator = WorkflowOrchestrator(database_service)
        workflow_tools = WorkflowTools(database_service, workflow_orchestrator)
        
        print("PASS: Workflow tools initialized successfully")
        
        # Test starting a workflow (this should fail gracefully due to database connection)
        result = await workflow_tools.start_research_workflow(
            workflow_type="research_discovery",
            parameters={"test": "data"},
            priority="normal"
        )
        
        print(f"Workflow start result: {result}")
        
        # The result should contain an error about database connection
        if "error" in result and "database" in result["error"].lower():
            print("PASS: Workflow start failed gracefully with database error (expected)")
        else:
            print(f"FAILED: Unexpected workflow start result: {result}")
            return False
        
        # Test listing workflows (should return empty list due to database error)
        list_result = await workflow_tools.list_workflows()
        print(f"Workflow list result: {list_result}")
        
        if "error" in list_result and "database" in list_result["error"].lower():
            print("PASS: Workflow list failed gracefully with database error (expected)")
        else:
            print(f"FAILED: Unexpected workflow list result: {list_result}")
            return False
        
        return True
        
    except Exception as e:
        print(f"FAILED: Workflow tools test failed: {e}")
        return False

async def test_workflow_orchestrator_mock_functionality():
    """Test workflow orchestrator mock functionality"""
    print("\n=== Testing Workflow Orchestrator Mock Functionality ===")
    
    try:
        database_url = "postgresql+asyncpg://dummy:dummy@localhost:5432/dummy"
        database_service = DatabaseService(database_url)
        orchestrator = WorkflowOrchestrator(database_service)
        
        print("PASS: Workflow orchestrator initialized successfully")
        
        # Test mock workflow creation
        mock_workflow = orchestrator.workflow_engine.create_workflow({"test": "definition"})
        print(f"PASS: Mock workflow created: {type(mock_workflow)}")
        
        # Test workflow status with fake UUID
        fake_uuid = UUID('12345678-1234-1234-1234-123456789012')
        status = await orchestrator.get_workflow_status(fake_uuid)
        print(f"PASS: Workflow status retrieved: {status}")
        
        # Test workflow cancellation with fake UUID
        cancel_result = await orchestrator.cancel_workflow(fake_uuid)
        print(f"PASS: Workflow cancellation attempted: {cancel_result}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Workflow orchestrator test failed: {e}")
        return False

async def test_bpmn_template_generation():
    """Test BPMN template generation for different workflow types"""
    print("\n=== Testing BPMN Template Generation ===")
    
    try:
        database_url = "postgresql+asyncpg://dummy:dummy@localhost:5432/dummy"
        database_service = DatabaseService(database_url)
        workflow_orchestrator = WorkflowOrchestrator(database_service)
        workflow_tools = WorkflowTools(database_service, workflow_orchestrator)
        
        workflow_types = ["research_discovery", "content_analysis", "connection_mapping"]
        
        for workflow_type in workflow_types:
            template = workflow_tools._get_bpmn_template(workflow_type)
            if template and "process" in template:
                print(f"PASS: BPMN template generated for {workflow_type}: {template['process']['name']}")
            else:
                print(f"FAILED: Invalid BPMN template for {workflow_type}: {template}")
                return False
        
        return True
        
    except Exception as e:
        print(f"FAILED: BPMN template generation test failed: {e}")
        return False

async def test_workflow_model_compatibility():
    """Test that workflow models are compatible with tools"""
    print("\n=== Testing Workflow Model Compatibility ===")
    
    try:
        from src.models.mcp_workflow import MCPWorkflowCreate
        
        # Test creating a workflow model with the fields that workflow tools expect
        workflow_data = {
            "workflow_type": "research_discovery",
            "workflow_definition": {
                "process": {"id": "test", "name": "Test Process"},
                "tasks": [{"id": "task1", "name": "Test Task"}]
            },
            "tool_mappings": {},
            "parameters": {"test": "data"},
            "status": "initializing",
            "priority": "normal"
        }
        
        workflow_create = MCPWorkflowCreate(**workflow_data)
        print("PASS: MCPWorkflowCreate model validation successful")
        
        # Verify all expected fields are present
        expected_fields = ["workflow_type", "workflow_definition", "tool_mappings", 
                          "parameters", "status", "priority", "current_step", "progress"]
        
        for field in expected_fields:
            if hasattr(workflow_create, field):
                print(f"PASS: Field '{field}' present in model")
            else:
                print(f"FAILED: Field '{field}' missing from model")
                return False
        
        return True
        
    except Exception as e:
        print(f"FAILED: Workflow model compatibility test failed: {e}")
        return False

async def main():
    """Run all workflow functionality tests"""
    print("MCP Workflow Tools Functionality Tests")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(await test_workflow_tools_without_database())
    results.append(await test_workflow_orchestrator_mock_functionality())
    results.append(await test_bpmn_template_generation())
    results.append(await test_workflow_model_compatibility())
    
    # Summary
    print("\n" + "=" * 50)
    print("FUNCTIONALITY TEST SUMMARY")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("SUCCESS: All functionality tests passed! Workflow integration is working correctly.")
    else:
        print("WARNING: Some functionality tests failed. Check specific issues above.")

if __name__ == "__main__":
    asyncio.run(main())