"""Test BrainForge MCP Tools using Server-Sent Events (SSE) protocol"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import httpx
import sseclient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPSSEClient:
    """MCP client using Server-Sent Events protocol"""
    
    def __init__(self, base_url: str = "http://localhost:8000/mcp"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.client_info = {
            "name": "BrainForge MCP Tester",
            "version": "1.0.0"
        }
    
    async def initialize(self) -> bool:
        """Initialize MCP session"""
        try:
            # MCP initialization requires SSE connection
            headers = {
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
            
            async with httpx.AsyncClient() as client:
                # First, try to establish SSE connection
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("SSE connection established successfully")
                    return True
                else:
                    logger.error(f"Failed to establish SSE connection: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def send_message(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send MCP message using SSE protocol"""
        try:
            message = {
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": method,
                "params": params
            }
            
            async with httpx.AsyncClient() as client:
                # For SSE, we need to use POST with specific headers
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
                
                response = await client.post(
                    self.base_url,
                    json=message,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    # Parse SSE response
                    client = sseclient.SSEClient(response)
                    for event in client.events():
                        if event.data:
                            return json.loads(event.data)
                
                logger.error(f"Message send failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Message send error: {e}")
            return {"error": str(e)}
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools"""
        params = {}
        response = await self.send_message("tools/list", params)
        return response.get("result", []) if "result" in response else []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool"""
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        response = await self.send_message("tools/call", params)
        return response.get("result", {}) if "result" in response else response


class MCPToolTester:
    """Comprehensive MCP tool tester"""
    
    def __init__(self):
        self.client = MCPSSEClient()
        self.test_results = {}
    
    async def test_all_tools(self) -> Dict[str, Any]:
        """Test all MCP tools comprehensively"""
        logger.info("Starting comprehensive MCP tool testing")
        
        # Initialize connection
        if not await self.client.initialize():
            return {"error": "Failed to initialize MCP connection"}
        
        # List available tools
        tools = await self.client.list_tools()
        logger.info(f"Available tools: {[tool.get('name', 'unknown') for tool in tools]}")
        
        # Test each tool category
        await self.test_search_tools()
        await self.test_note_tools()
        await self.test_workflow_tools()
        await self.test_export_tools()
        
        return self.test_results
    
    async def test_search_tools(self):
        """Test search-related tools"""
        logger.info("Testing search tools...")
        
        # Test search_library
        try:
            result = await self.client.call_tool("search_library", {
                "query": "artificial intelligence",
                "limit": 5,
                "similarity_threshold": 0.7
            })
            self.test_results["search_library"] = {
                "success": "result" in result or "error" not in result,
                "response": result
            }
            logger.info(f"search_library: {self.test_results['search_library']['success']}")
        except Exception as e:
            self.test_results["search_library"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"search_library failed: {e}")
        
        # Test discover_connections
        try:
            result = await self.client.call_tool("discover_connections", {
                "topic": "machine learning",
                "max_connections": 3
            })
            self.test_results["discover_connections"] = {
                "success": "result" in result or "error" not in result,
                "response": result
            }
            logger.info(f"discover_connections: {self.test_results['discover_connections']['success']}")
        except Exception as e:
            self.test_results["discover_connections"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"discover_connections failed: {e}")
        
        # Test get_library_stats
        try:
            result = await self.client.call_tool("get_library_stats", {})
            self.test_results["get_library_stats"] = {
                "success": "result" in result or "error" not in result,
                "response": result
            }
            logger.info(f"get_library_stats: {self.test_results['get_library_stats']['success']}")
        except Exception as e:
            self.test_results["get_library_stats"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"get_library_stats failed: {e}")
    
    async def test_note_tools(self):
        """Test note-related tools"""
        logger.info("Testing note tools...")
        
        # Test create_note
        try:
            result = await self.client.call_tool("create_note", {
                "title": "Test Note - AI Research",
                "content": "This is a test note created during MCP tool testing.",
                "tags": ["test", "ai", "research"],
                "metadata": {"test": True}
            })
            self.test_results["create_note"] = {
                "success": "result" in result or "error" not in result,
                "response": result
            }
            logger.info(f"create_note: {self.test_results['create_note']['success']}")
            
            # Store note ID for subsequent tests if creation was successful
            if self.test_results["create_note"]["success"]:
                note_data = result.get("result", result)
                self.note_id = note_data.get("id")
        except Exception as e:
            self.test_results["create_note"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"create_note failed: {e}")
        
        # Test update_note (if we have a note ID)
        if hasattr(self, 'note_id'):
            try:
                result = await self.client.call_tool("update_note", {
                    "note_id": self.note_id,
                    "title": "Updated Test Note",
                    "content": "This note has been updated during testing.",
                    "tags": ["test", "updated", "ai"]
                })
                self.test_results["update_note"] = {
                    "success": "result" in result or "error" not in result,
                    "response": result
                }
                logger.info(f"update_note: {self.test_results['update_note']['success']}")
            except Exception as e:
                self.test_results["update_note"] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"update_note failed: {e}")
        else:
            self.test_results["update_note"] = {
                "success": False,
                "error": "No note ID available from create_note"
            }
        
        # Test link_notes (create a second note first)
        try:
            result2 = await self.client.call_tool("create_note", {
                "title": "Second Test Note",
                "content": "This is a second test note for linking.",
                "tags": ["test", "link"]
            })
            
            if "result" in result2 or "error" not in result2:
                second_note_data = result2.get("result", result2)
                second_note_id = second_note_data.get("id")
                
                if hasattr(self, 'note_id') and second_note_id:
                    link_result = await self.client.call_tool("link_notes", {
                        "source_note_id": self.note_id,
                        "target_note_id": second_note_id,
                        "relationship_type": "related"
                    })
                    self.test_results["link_notes"] = {
                        "success": "result" in link_result or "error" not in link_result,
                        "response": link_result
                    }
                else:
                    self.test_results["link_notes"] = {
                        "success": False,
                        "error": "Missing note IDs for linking"
                    }
            else:
                self.test_results["link_notes"] = {
                    "success": False,
                    "error": "Failed to create second note for linking"
                }
            logger.info(f"link_notes: {self.test_results['link_notes']['success']}")
        except Exception as e:
            self.test_results["link_notes"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"link_notes failed: {e}")
    
    async def test_workflow_tools(self):
        """Test workflow-related tools"""
        logger.info("Testing workflow tools...")
        
        # Test start_research_workflow
        try:
            result = await self.client.call_tool("start_research_workflow", {
                "topic": "Artificial Intelligence Ethics",
                "max_sources": 3,
                "depth": "standard"
            })
            self.test_results["start_research_workflow"] = {
                "success": "result" in result or "error" not in result,
                "response": result
            }
            logger.info(f"start_research_workflow: {self.test_results['start_research_workflow']['success']}")
            
            # Store workflow ID for status check if workflow was started
            if self.test_results["start_research_workflow"]["success"]:
                workflow_data = result.get("result", result)
                self.workflow_id = workflow_data.get("workflow_id")
        except Exception as e:
            self.test_results["start_research_workflow"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"start_research_workflow failed: {e}")
        
        # Test get_workflow_status (if we have a workflow ID)
        if hasattr(self, 'workflow_id'):
            try:
                result = await self.client.call_tool("get_workflow_status", {
                    "workflow_id": self.workflow_id
                })
                self.test_results["get_workflow_status"] = {
                    "success": "result" in result or "error" not in result,
                    "response": result
                }
                logger.info(f"get_workflow_status: {self.test_results['get_workflow_status']['success']}")
            except Exception as e:
                self.test_results["get_workflow_status"] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"get_workflow_status failed: {e}")
        else:
            self.test_results["get_workflow_status"] = {
                "success": False,
                "error": "No workflow ID available from start_research_workflow"
            }
    
    async def test_export_tools(self):
        """Test export-related tools"""
        logger.info("Testing export tools...")
        
        # Test export_library
        try:
            result = await self.client.call_tool("export_library", {
                "format": "json",
                "include_metadata": True
            })
            self.test_results["export_library"] = {
                "success": "result" in result or "error" not in result,
                "response": result
            }
            logger.info(f"export_library: {self.test_results['export_library']['success']}")
        except Exception as e:
            self.test_results["export_library"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"export_library failed: {e}")
        
        # Test generate_documentation
        try:
            result = await self.client.call_tool("generate_documentation", {
                "topic": "AI Research Library",
                "format": "markdown",
                "detail_level": "comprehensive"
            })
            self.test_results["generate_documentation"] = {
                "success": "result" in result or "error" not in result,
                "response": result
            }
            logger.info(f"generate_documentation: {self.test_results['generate_documentation']['success']}")
        except Exception as e:
            self.test_results["generate_documentation"] = {
                "success": False,
                "error": str(e)
            }
            logger.error(f"generate_documentation failed: {e}")


async def main():
    """Main test function"""
    tester = MCPToolTester()
    results = await tester.test_all_tools()
    
    # Generate summary report
    print("\n" + "="*60)
    print("MCP TOOLS TESTING SUMMARY")
    print("="*60)
    
    total_tools = len(results)
    successful_tools = sum(1 for result in results.values() if result.get("success", False))
    
    print(f"Total Tools Tested: {total_tools}")
    print(f"Successful Tests: {successful_tools}")
    print(f"Success Rate: {(successful_tools/total_tools)*100:.1f}%")
    print("\nDetailed Results:")
    
    for tool_name, result in results.items():
        status = "✅ SUCCESS" if result.get("success", False) else "❌ FAILED"
        error = result.get("error", "No error")
        print(f"  {tool_name}: {status}")
        if not result.get("success", False):
            print(f"    Error: {error}")
    
    # Save detailed results to file
    with open("mcp_tools_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: mcp_tools_test_results.json")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())