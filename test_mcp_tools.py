#!/usr/bin/env python3
"""Comprehensive MCP Tools Test Script for BrainForge

This script tests all 10 MCP tools against the running BrainForge MCP server.
It exercises both successful operations and error conditions for each tool.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict
from uuid import UUID, uuid4

import httpx
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MCP Server Configuration
MCP_SERVER_URL = "http://localhost:8000/mcp"
TIMEOUT = 30.0


class MCPTestClient:
    """MCP Test Client for testing BrainForge MCP tools"""
    
    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.test_results = {}
    
    async def test_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single MCP tool"""
        try:
            logger.info(f"Testing tool: {tool_name}")
            logger.info(f"Parameters: {json.dumps(parameters, indent=2, default=str)}")
            
            # Make the MCP tool call
            response = await self.client.post(
                f"{self.base_url}/tools/{tool_name}",
                json=parameters
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ {tool_name} - SUCCESS")
                logger.info(f"Result: {json.dumps(result, indent=2, default=str)}")
                return {
                    "status": "success",
                    "result": result,
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                logger.error(f"❌ {tool_name} - FAILED (HTTP {response.status_code})")
                logger.error(f"Error: {response.text}")
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response.elapsed.total_seconds()
                }
                
        except Exception as e:
            logger.error(f"❌ {tool_name} - EXCEPTION: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "response_time": None
            }
    
    async def test_search_library(self) -> Dict[str, Any]:
        """Test search_library tool"""
        parameters = {
            "query": "machine learning algorithms",
            "limit": 5,
            "similarity_threshold": 0.7,
            "include_content": True
        }
        return await self.test_tool("search_library", parameters)
    
    async def test_discover_connections(self) -> Dict[str, Any]:
        """Test discover_connections tool"""
        parameters = {
            "note_id": None,  # Global discovery
            "connection_threshold": 0.6,
            "max_connections": 10
        }
        return await self.test_tool("discover_connections", parameters)
    
    async def test_get_library_stats(self) -> Dict[str, Any]:
        """Test get_library_stats tool"""
        parameters = {}  # No parameters needed
        return await self.test_tool("get_library_stats", parameters)
    
    async def test_create_note(self) -> Dict[str, Any]:
        """Test create_note tool"""
        parameters = {
            "title": "Test Note - Machine Learning Research",
            "content": "This is a test note created by the MCP tools test script. It contains information about machine learning algorithms and their applications.",
            "tags": ["test", "machine-learning", "research"],
            "source": "MCP Test Script"
        }
        return await self.test_tool("create_note", parameters)
    
    async def test_update_note(self, note_id: UUID) -> Dict[str, Any]:
        """Test update_note tool"""
        parameters = {
            "note_id": str(note_id),
            "title": "Updated Test Note - Advanced ML Research",
            "tags": ["test", "machine-learning", "research", "updated"]
        }
        return await self.test_tool("update_note", parameters)
    
    async def test_link_notes(self, source_note_id: UUID, target_note_id: UUID) -> Dict[str, Any]:
        """Test link_notes tool"""
        parameters = {
            "source_note_id": str(source_note_id),
            "target_note_id": str(target_note_id),
            "link_type": "semantic",
            "strength": 0.8,
            "description": "Test link between research notes"
        }
        return await self.test_tool("link_notes", parameters)
    
    async def test_start_research_workflow(self) -> Dict[str, Any]:
        """Test start_research_workflow tool"""
        parameters = {
            "workflow_type": "research_discovery",
            "parameters": {
                "topic": "neural networks",
                "max_sources": 5,
                "depth": "standard"
            },
            "priority": "normal"
        }
        return await self.test_tool("start_research_workflow", parameters)
    
    async def test_get_workflow_status(self, workflow_id: UUID) -> Dict[str, Any]:
        """Test get_workflow_status tool"""
        parameters = {
            "workflow_id": str(workflow_id)
        }
        return await self.test_tool("get_workflow_status", parameters)
    
    async def test_export_library(self) -> Dict[str, Any]:
        """Test export_library tool"""
        parameters = {
            "format": "json",
            "include_content": True,
            "include_links": True,
            "tags_filter": ["test"],
            "date_range": None
        }
        return await self.test_tool("export_library", parameters)
    
    async def test_generate_documentation(self) -> Dict[str, Any]:
        """Test generate_documentation tool"""
        parameters = {
            "output_format": "markdown",
            "include_examples": True,
            "include_api_reference": True,
            "template": None
        }
        return await self.test_tool("generate_documentation", parameters)
    
    async def test_error_conditions(self) -> Dict[str, Any]:
        """Test error conditions for various tools"""
        error_tests = {}
        
        # Test invalid search parameters
        logger.info("Testing error conditions...")
        
        # Invalid search parameters
        error_tests["search_invalid_params"] = await self.test_tool("search_library", {
            "query": "",  # Empty query
            "limit": -1,  # Invalid limit
            "similarity_threshold": 2.0  # Invalid threshold
        })
        
        # Invalid workflow type
        error_tests["workflow_invalid_type"] = await self.test_tool("start_research_workflow", {
            "workflow_type": "invalid_workflow_type",
            "parameters": {}
        })
        
        # Invalid export format
        error_tests["export_invalid_format"] = await self.test_tool("export_library", {
            "format": "invalid_format"
        })
        
        return error_tests
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all MCP tools"""
        logger.info("🚀 Starting comprehensive MCP tools test")
        logger.info(f"Target MCP server: {self.base_url}")
        
        test_results = {}
        
        try:
            # Test 1: Search and Discovery Tools
            logger.info("\n" + "="*50)
            logger.info("🔍 Testing Search and Discovery Tools")
            logger.info("="*50)
            
            test_results["search_library"] = await self.test_search_library()
            test_results["discover_connections"] = await self.test_discover_connections()
            test_results["get_library_stats"] = await self.test_get_library_stats()
            
            # Test 2: Note Management Tools
            logger.info("\n" + "="*50)
            logger.info("📝 Testing Note Management Tools")
            logger.info("="*50)
            
            create_result = await self.test_create_note()
            test_results["create_note"] = create_result
            
            # Extract note ID from create result for subsequent tests
            note_id = None
            if create_result["status"] == "success" and "result" in create_result:
                result_data = create_result["result"]
                if "note_id" in result_data:
                    note_id = UUID(result_data["note_id"])
                    logger.info(f"Created note ID: {note_id}")
            
            if note_id:
                test_results["update_note"] = await self.test_update_note(note_id)
                
                # Create a second note for linking
                second_note_result = await self.test_create_note()
                test_results["create_second_note"] = second_note_result
                
                if (second_note_result["status"] == "success" and 
                    "result" in second_note_result and 
                    "note_id" in second_note_result["result"]):
                    
                    second_note_id = UUID(second_note_result["result"]["note_id"])
                    test_results["link_notes"] = await self.test_link_notes(note_id, second_note_id)
            
            # Test 3: Workflow Tools
            logger.info("\n" + "="*50)
            logger.info("⚙️ Testing Workflow Tools")
            logger.info("="*50)
            
            workflow_result = await self.test_start_research_workflow()
            test_results["start_research_workflow"] = workflow_result
            
            # Extract workflow ID for status check
            workflow_id = None
            if workflow_result["status"] == "success" and "result" in workflow_result:
                result_data = workflow_result["result"]
                if "workflow_id" in result_data:
                    workflow_id = UUID(result_data["workflow_id"])
                    logger.info(f"Started workflow ID: {workflow_id}")
            
            if workflow_id:
                test_results["get_workflow_status"] = await self.test_get_workflow_status(workflow_id)
            
            # Test 4: Export Tools
            logger.info("\n" + "="*50)
            logger.info("📤 Testing Export Tools")
            logger.info("="*50)
            
            test_results["export_library"] = await self.test_export_library()
            test_results["generate_documentation"] = await self.test_generate_documentation()
            
            # Test 5: Error Conditions
            logger.info("\n" + "="*50)
            logger.info("❌ Testing Error Conditions")
            logger.info("="*50)
            
            test_results["error_conditions"] = await self.test_error_conditions()
            
            # Generate summary
            test_results["summary"] = self._generate_summary(test_results)
            
        except Exception as e:
            logger.error(f"Comprehensive test failed: {e}")
            test_results["overall_status"] = "failed"
            test_results["error"] = str(e)
        
        finally:
            await self.client.aclose()
        
        return test_results
    
    def _generate_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = 0
        successful_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for test_name, result in test_results.items():
            if test_name == "summary":
                continue
                
            if isinstance(result, dict) and "status" in result:
                total_tests += 1
                if result["status"] == "success":
                    successful_tests += 1
                elif result["status"] == "failed":
                    failed_tests += 1
                else:
                    error_tests += 1
        
        summary = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        logger.info("\n" + "="*50)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*50)
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Successful: {summary['successful_tests']}")
        logger.info(f"Failed: {summary['failed_tests']}")
        logger.info(f"Errors: {summary['error_tests']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info("="*50)
        
        return summary
    
    def save_results(self, results: Dict[str, Any], filename: str = "mcp_test_results.json"):
        """Save test results to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Convert UUID objects to strings for JSON serialization
                def convert_uuids(obj):
                    if isinstance(obj, UUID):
                        return str(obj)
                    elif isinstance(obj, dict):
                        return {k: convert_uuids(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_uuids(v) for v in obj]
                    return obj
                
                json.dump(convert_uuids(results), f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


async def main():
    """Main test execution function"""
    client = MCPTestClient()
    
    try:
        # Test server connectivity first
        logger.info("Testing MCP server connectivity...")
        try:
            response = await client.client.get(f"{MCP_SERVER_URL}/health")
            if response.status_code == 200:
                logger.info("✅ MCP server is accessible")
            else:
                logger.warning(f"⚠️ MCP server returned status: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Cannot connect to MCP server: {e}")
            logger.error("Make sure the MCP server is running at: http://localhost:8000/mcp")
            return
        
        # Run comprehensive test
        results = await client.run_comprehensive_test()
        
        # Save results
        client.save_results(results)
        
        # Print final status
        summary = results.get("summary", {})
        success_rate = summary.get("success_rate", 0)
        
        if success_rate >= 80:
            logger.info("🎉 MCP Tools Test: PASSED")
        elif success_rate >= 50:
            logger.info("⚠️ MCP Tools Test: PARTIAL SUCCESS")
        else:
            logger.info("❌ MCP Tools Test: FAILED")
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
    finally:
        await client.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())