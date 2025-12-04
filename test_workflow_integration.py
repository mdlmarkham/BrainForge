#!/usr/bin/env python3
"""Test script to validate MCP workflow integration issues"""

import asyncio
import logging
from uuid import UUID

from src.mcp.workflows.integration import WorkflowOrchestrator
from src.mcp.tools.workflows import WorkflowTools
from src.services.generic_database_service import DatabaseService
from src.models.mcp_workflow import MCPWorkflowCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_workflow_model_validation():
    """Test MCPWorkflowCreate validation issues"""
    print("=== Testing MCPWorkflowCreate Validation ===")
    
    try:
        # Test creating a workflow with minimal data (like the workflow tools do)
        workflow_data = {
            "workflow_type": "research_discovery",
            "parameters": {"test": "data"},
            "status": "initializing",
            "priority": "normal"
        }
        
        # This should fail with validation errors
        workflow_create = MCPWorkflowCreate(**workflow_data)
        print("PASS: MCPWorkflowCreate validation passed (unexpected)")
        return True
        
    except Exception as e:
        print(f"FAILED: MCPWorkflowCreate validation failed (expected): {str(e)}")
        return False

async def test_database_service_methods():
    """Test DatabaseService method compatibility"""
    print("\n=== Testing DatabaseService Method Compatibility ===")
    
    try:
        # Create a database service instance
        database_url = "postgresql+asyncpg://brainforge:brainforge@localhost:5432/brainforge"
        database_service = DatabaseService(database_url)
        
        # Test if session() method exists (used in workflow tools)
        if hasattr(database_service, 'session'):
            print("PASS: DatabaseService has session() method")
            
            # Test session context manager
            async with database_service.session() as session:
                print("PASS: DatabaseService session context manager works")
                
                # Test if create method accepts table name as string
                test_data = {"test": "data"}
                try:
                    # This should work with the new generic service
                    result = await database_service.create(session, "mcp_workflows", test_data)
                    print("PASS: DatabaseService.create() with table name worked")
                    return True
                except Exception as e:
                    print(f"FAILED: DatabaseService.create() with table name failed: {e}")
                    return False
        else:
            print("FAILED: DatabaseService missing session() method")
            return False
        
    except Exception as e:
        print(f"FAILED: DatabaseService test failed: {e}")
        return False

async def test_workflow_tools_initialization():
    """Test WorkflowTools initialization and basic functionality"""
    print("\n=== Testing WorkflowTools Initialization ===")
    
    try:
        database_url = "postgresql+asyncpg://brainforge:brainforge@localhost:5432/brainforge"
        database_service = DatabaseService(database_url)
        workflow_orchestrator = WorkflowOrchestrator(database_service)
        workflow_tools = WorkflowTools(database_service, workflow_orchestrator)
        
        print("PASS: WorkflowTools initialization successful")
        
        # Test BPMN template generation
        template = workflow_tools._get_bpmn_template("research_discovery")
        print(f"PASS: BPMN template generated: {template}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: WorkflowTools initialization failed: {e}")
        return False

async def test_workflow_orchestrator():
    """Test WorkflowOrchestrator functionality"""
    print("\n=== Testing WorkflowOrchestrator ===")
    
    try:
        database_url = "postgresql+asyncpg://brainforge:brainforge@localhost:5432/brainforge"
        database_service = DatabaseService(database_url)
        orchestrator = WorkflowOrchestrator(database_service)
        
        print("PASS: WorkflowOrchestrator initialization successful")
        
        # Test mock workflow creation
        mock_workflow = orchestrator.workflow_engine.create_workflow({"test": "definition"})
        print(f"PASS: Mock workflow created: {mock_workflow}")
        
        # Test workflow status method with fake UUID
        fake_uuid = UUID('12345678-1234-1234-1234-123456789012')
        status = await orchestrator.get_workflow_status(fake_uuid)
        print(f"PASS: Workflow status retrieved: {status}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: WorkflowOrchestrator test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("MCP Workflow Integration Diagnostic Tests")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(await test_workflow_model_validation())
    results.append(await test_database_service_methods())
    results.append(await test_workflow_tools_initialization())
    results.append(await test_workflow_orchestrator())
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("SUCCESS: All tests passed! Workflow integration is functional.")
    else:
        print("WARNING: Some tests failed. Workflow integration needs fixes.")

if __name__ == "__main__":
    asyncio.run(main())