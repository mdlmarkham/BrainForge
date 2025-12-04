#!/usr/bin/env python3
"""
BrainForge MCP Tools Test Client (Corrected)

This script tests all 10 MCP tools using the correct JSON-RPC 2.0 protocol
for FastMCP HTTP transport.

The MCP server should be running at http://localhost:8000
"""

import asyncio
import json
import logging
from typing import Any, Dict, List
from uuid import UUID, uuid4

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MCPTestClient:
    """Test client for BrainForge MCP tools using JSON-RPC 2.0 protocol"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.session_id = None
    
    async def initialize(self):
        """Initialize the MCP session"""
        try:
            # FastMCP HTTP transport uses JSON-RPC 2.0 protocol
            # First, let's test if the server is accessible
            response = await self.client.get(f"{self.base_url}/")
            logger.info(f"Server root response: {response.status_code}")
            
            # Try to get the tools list
            tools_response = await self.client.get(f"{self.base_url}/tools")
            logger.info(f"Tools endpoint response: {response.status_code}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            return False
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool using JSON-RPC 2.0 protocol"""
        try:
            # JSON-RPC 2.0 request format
            request_data = {
                "jsonrpc": "2.0",
                "method": tool_name,
                "params": params,
                "id": str(uuid4())
            }
            
            logger.info(f"Calling tool {tool_name} with params: {params}")
            
            response = await self.client.post(
                f"{self.base_url}/",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Tool response: {result}")
                return result
            else:
                logger.error(f"HTTP error: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def test_search_library(self) -> Dict[str, Any]:
        """Test search_library tool"""
        params = {
            "query": "machine learning",
            "limit": 5,
            "similarity_threshold": 0.8
        }
        return await self.call_tool("search_library", params)
    
    async def test_discover_connections(self) -> Dict[str, Any]:
        """Test discover_connections tool"""
        params = {
            "note_id": None  # Global connections
        }
        return await self.call_tool("discover_connections", params)
    
    async def test_get_library_stats(self) -> Dict[str, Any]:
        """Test get_library_stats tool"""
        params = {}  # No parameters needed
        return await self.call_tool("get_library_stats", params)
    
    async def test_create_note(self) -> Dict[str, Any]:
        """Test create_note tool"""
        params = {
            "title": "Test Note for MCP Tool Testing",
            "content": "This is a test note created by the MCP test client",
            "tags": ["test", "mcp", "integration"]
        }
        return await self.call_tool("create_note", params)
    
    async def test_update_note(self, note_id: UUID) -> Dict[str, Any]:
        """Test update_note tool"""
        params = {
            "note_id": str(note_id),
            "title": "Updated Test Note",
            "content": "This note has been updated by the MCP test client"
        }
        return await self.call_tool("update_note", params)
    
    async def test_link_notes(self, note1_id: UUID, note2_id: UUID) -> Dict[str, Any]:
        """Test link_notes tool"""
        params = {
            "source_note_id": str(note1_id),
            "target_note_id": str(note2_id),
            "relationship_type": "related"
        }
        return await self.call_tool("link_notes", params)
    
    async def test_start_research_workflow(self) -> Dict[str, Any]:
        """Test start_research_workflow tool"""
        params = {
            "workflow_type": "research_discovery",
            "parameters": {
                "topic": "AI research trends",
                "max_sources": 5,
                "depth": "standard"
            }
        }
        return await self.call_tool("start_research_workflow", params)
    
    async def test_get_workflow_status(self, workflow_id: UUID) -> Dict[str, Any]:
        """Test get_workflow_status tool"""
        params = {
            "workflow_id": str(workflow_id)
        }
        return await self.call_tool("get_workflow_status", params)
    
    async def test_export_library(self) -> Dict[str, Any]:
        """Test export_library tool"""
        params = {
            "format": "json",
            "include_content": True
        }
        return await self.call_tool("export_library", params)
    
    async def test_generate_documentation(self) -> Dict[str, Any]:
        """Test generate_documentation tool"""
        params = {
            "output_format": "markdown"
        }
        return await self.call_tool("generate_documentation", params)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def main():
    """Main test function"""
    logger.info("Starting BrainForge MCP Tools Test")
    
    # Create test client
    client = MCPTestClient("http://localhost:8000")
    
    try:
        # Initialize client
        if not await client.initialize():
            logger.error("Failed to initialize MCP client")
            return
        
        # Test results storage
        test_results = {}
        
        # Test 1: Search library
        logger.info("=== Testing search_library tool ===")
        test_results["search_library"] = await client.test_search_library()
        
        # Test 2: Discover connections
        logger.info("=== Testing discover_connections tool ===")
        test_results["discover_connections"] = await client.test_discover_connections()
        
        # Test 3: Get library stats
        logger.info("=== Testing get_library_stats tool ===")
        test_results["get_library_stats"] = await client.test_get_library_stats()
        
        # Test 4: Create note
        logger.info("=== Testing create_note tool ===")
        create_result = await client.test_create_note()
        test_results["create_note"] = create_result
        
        # Extract note ID for subsequent tests if creation was successful
        note_id = None
        if create_result and "result" in create_result and "id" in create_result["result"]:
            note_id = UUID(create_result["result"]["id"])
            logger.info(f"Created note with ID: {note_id}")
        
        # Test 5: Update note (if note was created)
        if note_id:
            logger.info("=== Testing update_note tool ===")
            test_results["update_note"] = await client.test_update_note(note_id)
        
        # Test 6: Link notes (create another note first)
        logger.info("=== Testing link_notes tool ===")
        if note_id:
            # Create a second note for linking
            second_note_result = await client.test_create_note()
            test_results["create_second_note"] = second_note_result
            
            if second_note_result and "result" in second_note_result and "id" in second_note_result["result"]:
                second_note_id = UUID(second_note_result["result"]["id"])
                test_results["link_notes"] = await client.test_link_notes(note_id, second_note_id)
        
        # Test 7: Start research workflow
        logger.info("=== Testing start_research_workflow tool ===")
        workflow_result = await client.test_start_research_workflow()
        test_results["start_research_workflow"] = workflow_result
        
        # Extract workflow ID for status check
        workflow_id = None
        if workflow_result and "result" in workflow_result and "id" in workflow_result["result"]:
            workflow_id = UUID(workflow_result["result"]["id"])
        
        # Test 8: Get workflow status (if workflow was started)
        if workflow_id:
            logger.info("=== Testing get_workflow_status tool ===")
            test_results["get_workflow_status"] = await client.test_get_workflow_status(workflow_id)
        
        # Test 9: Export library
        logger.info("=== Testing export_library tool ===")
        test_results["export_library"] = await client.test_export_library()
        
        # Test 10: Generate documentation
        logger.info("=== Testing generate_documentation tool ===")
        test_results["generate_documentation"] = await client.test_generate_documentation()
        
        # Generate summary
        logger.info("=== Test Summary ===")
        successful_tests = 0
        failed_tests = 0
        
        for tool_name, result in test_results.items():
            if result and "error" not in result:
                successful_tests += 1
                logger.info(f"✓ {tool_name}: SUCCESS")
            else:
                failed_tests += 1
                logger.error(f"✗ {tool_name}: FAILED - {result.get('error', 'Unknown error')}")
        
        logger.info(f"Test Results: {successful_tests} successful, {failed_tests} failed")
        
        # Save detailed results to file
        with open("mcp_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        logger.info("Detailed results saved to mcp_test_results.json")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())