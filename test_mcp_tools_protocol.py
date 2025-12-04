#!/usr/bin/env python3
"""
BrainForge MCP Tools Test Client
Tests all 10 MCP tools using the correct MCP protocol structure
"""

import asyncio
import json
import logging
from typing import Any, Dict, List
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPProtocolClient:
    """MCP Protocol Client for testing BrainForge MCP tools"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.session_id = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the MCP session"""
        try:
            # MCP initialization request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "BrainForge Test Client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self.client.post(
                self.base_url,
                json=init_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    self.initialized = True
                    logger.info("MCP session initialized successfully")
                    return True
                else:
                    logger.error(f"Initialization failed: {result.get('error', 'Unknown error')}")
            else:
                logger.error(f"HTTP error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Initialization error: {e}")
        
        return False
    
    async def list_tools(self):
        """List available tools"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            response = await self.client.post(
                self.base_url,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    tools = result["result"]["tools"]
                    logger.info(f"Available tools: {[tool['name'] for tool in tools]}")
                    return tools
                else:
                    logger.error(f"Tool listing failed: {result.get('error', 'Unknown error')}")
            else:
                logger.error(f"HTTP error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Tool listing error: {e}")
        
        return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await self.client.post(
                self.base_url,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    return result["result"]
                else:
                    error_msg = result.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"Tool call failed: {error_msg}")
                    return {"error": error_msg}
            else:
                logger.error(f"HTTP error: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()


class MCPToolTester:
    """Comprehensive tester for all BrainForge MCP tools"""
    
    def __init__(self):
        self.client = MCPProtocolClient()
        self.test_results = {}
    
    async def test_all_tools(self):
        """Test all 10 MCP tools"""
        logger.info("Starting comprehensive MCP tool testing")
        
        # Initialize the client
        if not await self.client.initialize():
            logger.error("Failed to initialize MCP client")
            return False
        
        # List available tools
        tools = await self.client.list_tools()
        if not tools:
            logger.error("No tools available")
            return False
        
        logger.info(f"Found {len(tools)} tools to test")
        
        # Test each tool with appropriate test data
        test_cases = [
            # Search and discovery tools
            {
                "name": "search_library",
                "arguments": {
                    "query": "artificial intelligence",
                    "limit": 5,
                    "similarity_threshold": 0.7
                },
                "description": "Search library using semantic search"
            },
            {
                "name": "discover_connections",
                "arguments": {
                    "topic": "machine learning",
                    "max_connections": 3
                },
                "description": "Discover semantic connections"
            },
            {
                "name": "get_library_stats",
                "arguments": {},
                "description": "Get library statistics"
            },
            # Note management tools
            {
                "name": "create_note",
                "arguments": {
                    "title": "Test Note - AI Research",
                    "content": "This is a test note about artificial intelligence research.",
                    "tags": ["ai", "research", "test"]
                },
                "description": "Create a new note"
            },
            {
                "name": "update_note",
                "arguments": {
                    "note_id": "test-note-id",  # Will be replaced with actual ID
                    "title": "Updated Test Note",
                    "content": "Updated content about AI research"
                },
                "description": "Update an existing note"
            },
            {
                "name": "link_notes",
                "arguments": {
                    "source_note_id": "note-1",
                    "target_note_id": "note-2",
                    "relationship_type": "related"
                },
                "description": "Link notes semantically"
            },
            # Workflow tools
            {
                "name": "start_research_workflow",
                "arguments": {
                    "topic": "neural networks",
                    "max_sources": 5,
                    "depth": "standard"
                },
                "description": "Start research workflow"
            },
            {
                "name": "get_workflow_status",
                "arguments": {
                    "workflow_id": "test-workflow-id"
                },
                "description": "Get workflow status"
            },
            # Export tools
            {
                "name": "export_library",
                "arguments": {
                    "format": "json",
                    "include_metadata": True
                },
                "description": "Export library data"
            },
            {
                "name": "generate_documentation",
                "arguments": {
                    "format": "markdown",
                    "include_examples": True
                },
                "description": "Generate documentation"
            }
        ]
        
        # Test each tool
        for test_case in test_cases:
            tool_name = test_case["name"]
            logger.info(f"Testing tool: {tool_name} - {test_case['description']}")
            
            result = await self.client.call_tool(tool_name, test_case["arguments"])
            self.test_results[tool_name] = {
                "description": test_case["description"],
                "arguments": test_case["arguments"],
                "result": result,
                "success": "error" not in result
            }
            
            if "error" in result:
                logger.warning(f"Tool {tool_name} failed: {result['error']}")
            else:
                logger.info(f"Tool {tool_name} succeeded")
        
        await self.client.close()
        return True
    
    def generate_report(self):
        """Generate a comprehensive test report"""
        report = {
            "summary": {
                "total_tools": len(self.test_results),
                "successful_tools": sum(1 for r in self.test_results.values() if r["success"]),
                "failed_tools": sum(1 for r in self.test_results.values() if not r["success"])
            },
            "detailed_results": self.test_results
        }
        
        # Print summary
        print("\n" + "="*60)
        print("BRAINFORGE MCP TOOLS TEST REPORT")
        print("="*60)
        print(f"Total Tools Tested: {report['summary']['total_tools']}")
        print(f"Successful: {report['summary']['successful_tools']}")
        print(f"Failed: {report['summary']['failed_tools']}")
        print("="*60)
        
        # Print detailed results
        for tool_name, result in self.test_results.items():
            status = "✓ SUCCESS" if result["success"] else "✗ FAILED"
            print(f"\n{tool_name}: {status}")
            print(f"Description: {result['description']}")
            if not result["success"]:
                print(f"Error: {result['result'].get('error', 'Unknown error')}")
            else:
                print(f"Result type: {type(result['result']).__name__}")
                if isinstance(result['result'], dict):
                    print(f"Keys returned: {list(result['result'].keys())}")
        
        return report


async def main():
    """Main test function"""
    tester = MCPToolTester()
    
    try:
        success = await tester.test_all_tools()
        if success:
            report = tester.generate_report()
            
            # Save detailed results to file
            with open("mcp_tools_test_results.json", "w") as f:
                json.dump(report, f, indent=2)
            
            print(f"\nDetailed results saved to: mcp_tools_test_results.json")
            
        else:
            print("Testing failed - check logs for details")
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())