#!/usr/bin/env python3
"""
Comprehensive test script for BrainForge MCP tools using FastMCP client.

This script tests all 10 MCP tools against the running BrainForge MCP server
at http://localhost:8000/mcp.

Usage:
    python test_mcp_tools_fastmcp.py
"""

import asyncio
import json
import sys
from typing import Dict, Any, List
from fastmcp import Client


class MCPToolTester:
    """Test class for BrainForge MCP tools."""
    
    def __init__(self, server_url: str = "http://localhost:8000/mcp"):
        self.server_url = server_url
        self.client = Client(server_url)
        self.test_results = {}
    
    async def list_tools(self) -> List[str]:
        """List all available tools on the MCP server."""
        try:
            async with self.client:
                tools = await self.client.list_tools()
                tool_names = [tool.name for tool in tools]
                print(f"Available tools: {tool_names}")
                return tool_names
        except Exception as e:
            print(f"Error listing tools: {e}")
            return []
    
    async def test_search_library(self) -> Dict[str, Any]:
        """Test the search_library tool."""
        try:
            async with self.client:
                result = await self.client.call_tool(
                    name="search_library",
                    arguments={
                        "query": "artificial intelligence",
                        "limit": 5,
                        "similarity_threshold": 0.7
                    }
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_discover_connections(self) -> Dict[str, Any]:
        """Test the discover_connections tool."""
        try:
            async with self.client:
                result = await self.client.call_tool(
                    name="discover_connections",
                    arguments={
                        "note_id": None,  # Global discovery
                        "connection_threshold": 0.6,
                        "max_connections": 3
                    }
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_get_library_stats(self) -> Dict[str, Any]:
        """Test the get_library_stats tool."""
        try:
            async with self.client:
                result = await self.client.call_tool(
                    name="get_library_stats",
                    arguments={}
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_create_note(self) -> Dict[str, Any]:
        """Test the create_note tool."""
        try:
            async with self.client:
                result = await self.client.call_tool(
                    name="create_note",
                    arguments={
                        "title": "Test Note - AI Research",
                        "content": "This is a test note created via MCP tool testing.",
                        "tags": ["test", "ai", "research"],
                        "source": "MCP Test Suite"
                    }
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_update_note(self) -> Dict[str, Any]:
        """Test the update_note tool."""
        try:
            # First create a note to update
            create_result = await self.test_create_note()
            if not create_result["success"]:
                return {
                    "success": False,
                    "error": "Could not create note for update test",
                    "create_error": create_result.get("error")
                }
            
            # Extract note ID from create result
            note_data = create_result.get("result", {})
            note_id = note_data.get("id") if isinstance(note_data, dict) else None
            
            if not note_id:
                return {
                    "success": False,
                    "error": "Could not extract note ID from create result",
                    "create_result": create_result
                }
            
            async with self.client:
                result = await self.client.call_tool(
                    name="update_note",
                    arguments={
                        "note_id": note_id,
                        "title": "Updated Test Note - AI Research",
                        "content": "This note has been updated via MCP tool testing.",
                        "tags": ["test", "ai", "research", "updated"]
                    }
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_link_notes(self) -> Dict[str, Any]:
        """Test the link_notes tool."""
        try:
            # Create two notes to link
            note1_result = await self.test_create_note()
            note2_result = await self.test_create_note()
            
            if not note1_result["success"] or not note2_result["success"]:
                return {
                    "success": False,
                    "error": "Could not create notes for linking test",
                    "note1_error": note1_result.get("error"),
                    "note2_error": note2_result.get("error")
                }
            
            # Extract note IDs
            note1_data = note1_result.get("result", {})
            note2_data = note2_result.get("result", {})
            note1_id = note1_data.get("id") if isinstance(note1_data, dict) else None
            note2_id = note2_data.get("id") if isinstance(note2_data, dict) else None
            
            if not note1_id or not note2_id:
                return {
                    "success": False,
                    "error": "Could not extract note IDs from create results",
                    "note1_result": note1_result,
                    "note2_result": note2_result
                }
            
            async with self.client:
                result = await self.client.call_tool(
                    name="link_notes",
                    arguments={
                        "source_note_id": note1_id,
                        "target_note_id": note2_id,
                        "link_type": "semantic",
                        "strength": 0.8,
                        "description": "Test link between notes"
                    }
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_start_research_workflow(self) -> Dict[str, Any]:
        """Test the start_research_workflow tool."""
        try:
            async with self.client:
                result = await self.client.call_tool(
                    name="start_research_workflow",
                    arguments={
                        "workflow_type": "research_discovery",
                        "parameters": {"topic": "impact of artificial intelligence on healthcare"},
                        "priority": "normal"
                    }
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_get_workflow_status(self) -> Dict[str, Any]:
        """Test the get_workflow_status tool."""
        try:
            # First start a workflow to get status for
            workflow_result = await self.test_start_research_workflow()
            if not workflow_result["success"]:
                return {
                    "success": False,
                    "error": "Could not start workflow for status test",
                    "workflow_error": workflow_result.get("error")
                }
            
            # Extract workflow ID
            workflow_data = workflow_result.get("result", {})
            workflow_id = workflow_data.get("workflow_id") if isinstance(workflow_data, dict) else None
            
            if not workflow_id:
                return {
                    "success": False,
                    "error": "Could not extract workflow ID from start result",
                    "workflow_result": workflow_result
                }
            
            async with self.client:
                result = await self.client.call_tool(
                    name="get_workflow_status",
                    arguments={
                        "workflow_id": workflow_id
                    }
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_export_library(self) -> Dict[str, Any]:
        """Test the export_library tool."""
        try:
            async with self.client:
                result = await self.client.call_tool(
                    name="export_library",
                    arguments={
                        "format": "json",
                        "include_content": True,
                        "include_links": True,
                        "tags_filter": ["test"],
                        "date_range": None
                    }
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_generate_documentation(self) -> Dict[str, Any]:
        """Test the generate_documentation tool."""
        try:
            async with self.client:
                result = await self.client.call_tool(
                    name="generate_documentation",
                    arguments={
                        "output_format": "markdown",
                        "include_examples": True,
                        "include_api_reference": True,
                        "template": None
                    }
                )
                return {
                    "success": True,
                    "result": result.data if hasattr(result, 'data') else result,
                    "content": result.content if hasattr(result, 'content') else None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all MCP tool tests and return comprehensive results."""
        print(f"Starting MCP tool tests against {self.server_url}")
        print("=" * 60)
        
        # List available tools first
        available_tools = await self.list_tools()
        print(f"Found {len(available_tools)} tools: {available_tools}")
        print()
        
        # Test each tool
        test_methods = [
            ("search_library", self.test_search_library),
            ("discover_connections", self.test_discover_connections),
            ("get_library_stats", self.test_get_library_stats),
            ("create_note", self.test_create_note),
            ("update_note", self.test_update_note),
            ("link_notes", self.test_link_notes),
            ("start_research_workflow", self.test_start_research_workflow),
            ("get_workflow_status", self.test_get_workflow_status),
            ("export_library", self.test_export_library),
            ("generate_documentation", self.test_generate_documentation),
        ]
        
        results = {}
        for tool_name, test_method in test_methods:
            print(f"Testing {tool_name}...")
            result = await test_method()
            results[tool_name] = result
            
            if result["success"]:
                print(f"  [SUCCESS] {tool_name}: SUCCESS")
                if "result" in result and result["result"]:
                    result_summary = str(result["result"])[:100] + "..." if len(str(result["result"])) > 100 else str(result["result"])
                    print(f"    Result: {result_summary}")
            else:
                print(f"  [FAILED] {tool_name}: FAILED")
                print(f"    Error: {result['error']}")
                if "error_type" in result:
                    print(f"    Error Type: {result['error_type']}")
            print()
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("MCP TOOLS TEST REPORT")
        report.append("=" * 60)
        report.append(f"Server: {self.server_url}")
        report.append(f"Total Tools Tested: {len(results)}")
        
        successful_tests = [name for name, result in results.items() if result["success"]]
        failed_tests = [name for name, result in results.items() if not result["success"]]
        
        report.append(f"Successful: {len(successful_tests)}")
        report.append(f"Failed: {len(failed_tests)}")
        report.append("")
        
        if successful_tests:
            report.append("SUCCESSFUL TESTS:")
            report.append("-" * 30)
            for tool_name in successful_tests:
                result = results[tool_name]
                report.append(f"[SUCCESS] {tool_name}")
                if "result" in result and result["result"]:
                    result_str = str(result["result"])
                    if len(result_str) > 100:
                        result_str = result_str[:100] + "..."
                    report.append(f"  Result: {result_str}")
                report.append("")
        
        if failed_tests:
            report.append("FAILED TESTS:")
            report.append("-" * 30)
            for tool_name in failed_tests:
                result = results[tool_name]
                report.append(f"[FAILED] {tool_name}")
                report.append(f"  Error: {result['error']}")
                if "error_type" in result:
                    report.append(f"  Error Type: {result['error_type']}")
                report.append("")
        
        return "\n".join(report)


async def main():
    """Main test function."""
    tester = MCPToolTester()
    
    try:
        results = await tester.run_all_tests()
        report = tester.generate_report(results)
        
        print("TEST COMPLETED")
        print("=" * 60)
        print(report)
        
        # Save detailed results to file
        with open("mcp_tools_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print("\nDetailed results saved to mcp_tools_test_results.json")
        
        # Exit with appropriate code
        successful_tests = len([name for name, result in results.items() if result["success"]])
        if successful_tests == len(results):
            print("All tests passed! [SUCCESS]")
            sys.exit(0)
        else:
            print(f"{successful_tests}/{len(results)} tests passed. Some tests failed. [FAILED]")
            sys.exit(1)
            
    except Exception as e:
        print(f"Critical error during testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())