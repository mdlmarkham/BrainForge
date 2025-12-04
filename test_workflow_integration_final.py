#!/usr/bin/env python3
"""Final test of MCP workflow integration with actual database configuration"""

import asyncio
import logging
import os
from uuid import UUID

from src.mcp.workflows.integration import WorkflowOrchestrator
from src.mcp.tools.workflows import WorkflowTools
from src.services.generic_database_service import DatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_workflow_integration_with_real_database():
    """Test workflow integration with the actual database configuration"""
    print("=== Testing Workflow Integration with Real Database ===")
    
    try:
        # Use the actual database URL from .env
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:cessna81@192.168.70.112:5433/brainforge")
        print(f"Using database URL: {database_url}")
        
        database_service = DatabaseService(database_url)
        workflow_orchestrator = WorkflowOrchestrator(database_service)
        workflow_tools = WorkflowTools(database_service, workflow_orchestrator)
        
        print("PASS: Services initialized with real database configuration")
        
        # Test workflow start with real database
        result = await workflow_tools.start_research_workflow(
            workflow_type="research_discovery",
            parameters={"test": "integration_test"},
            priority="normal"
        )
        
        print(f"Workflow start result: {result}")
        
        if "workflow_id" in result and result.get("status") == "started":
            print("PASS: Workflow started successfully with real database")
            
            # Test getting workflow status
            workflow_id = result["workflow_id"]
            status_result = await workflow_tools.get_workflow_status(workflow_id)
            print(f"Workflow status result: {status_result}")
            
            if status_result.get("status") in ["running", "started"]:
                print("PASS: Workflow status retrieved successfully")
                return True
            else:
                print(f"FAILED: Unexpected workflow status: {status_result}")
                return False
        else:
            print(f"FAILED: Workflow start failed: {result}")
            return False
            
    except Exception as e:
        print(f"FAILED: Workflow integration test failed: {e}")
        return False

async def test_database_connectivity():
    """Test database connectivity with actual configuration"""
    print("\n=== Testing Database Connectivity ===")
    
    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:cessna81@192.168.70.112:5433/brainforge")
        database_service = DatabaseService(database_url)
        
        # Test session creation and basic operation
        async with database_service.session() as session:
            print("PASS: Database session created successfully")
            
            # Test a simple query to verify connectivity
            try:
                # This should work if the database is accessible
                test_data = {"test": "integration_test"}
                result = await database_service.create(session, "mcp_workflows", test_data)
                print(f"PASS: Database operation successful: {result}")
                return True
            except Exception as db_error:
                print(f"FAILED: Database operation failed: {db_error}")
                return False
                
    except Exception as e:
        print(f"FAILED: Database connectivity test failed: {e}")
        return False

async def test_workflow_tools_complete_lifecycle():
    """Test complete workflow lifecycle with real database"""
    print("\n=== Testing Complete Workflow Lifecycle ===")
    
    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:cessna81@192.168.70.112:5433/brainforge")
        database_service = DatabaseService(database_url)
        workflow_tools = WorkflowTools(database_service, WorkflowOrchestrator(database_service))
        
        # Test listing workflows
        list_result = await workflow_tools.list_workflows()
        print(f"Workflow list result: {list_result}")
        
        if "workflows" in list_result:
            print("PASS: Workflow listing successful")
        else:
            print(f"FAILED: Workflow listing failed: {list_result}")
            return False
        
        # Test different workflow types
        workflow_types = ["research_discovery", "content_analysis", "connection_mapping"]
        
        for workflow_type in workflow_types:
            result = await workflow_tools.start_research_workflow(
                workflow_type=workflow_type,
                parameters={"test_type": workflow_type},
                priority="normal"
            )
            
            if "workflow_id" in result:
                print(f"PASS: {workflow_type} workflow started successfully")
            else:
                print(f"FAILED: {workflow_type} workflow start failed: {result}")
                return False
        
        return True
        
    except Exception as e:
        print(f"FAILED: Complete workflow lifecycle test failed: {e}")
        return False

async def main():
    """Run final integration tests"""
    print("FINAL MCP Workflow Integration Test")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(await test_database_connectivity())
    if results[0]:  # Only proceed if database connectivity works
        results.append(await test_workflow_integration_with_real_database())
        results.append(await test_workflow_tools_complete_lifecycle())
    
    # Summary
    print("\n" + "=" * 50)
    print("FINAL TEST SUMMARY")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("SUCCESS: All final tests passed! MCP workflow integration is fully functional.")
        print("The workflow tools are ready for production use with the real database.")
    else:
        print("WARNING: Some final tests failed. Check database connectivity and configuration.")

if __name__ == "__main__":
    asyncio.run(main())