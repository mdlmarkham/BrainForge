"""BrainForge MCP Server Implementation"""

import logging
from typing import Any
from uuid import UUID

from fastmcp import FastMCP

from ..models.mcp_execution import MCPExecution, MCPExecutionCreate
from ..models.mcp_session import MCPSession, MCPSessionCreate
from ..services.database import DatabaseService
from .auth.session import SessionManager
from .tools.export import ExportTools
from .tools.notes import NoteTools
from .tools.search import SearchTools
from .tools.workflows import WorkflowTools
from .workflows.integration import WorkflowOrchestrator


class BrainForgeMCP:
    """Main MCP server for BrainForge library interface"""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        self.session_manager = SessionManager(database_service)
        self.workflow_orchestrator = WorkflowOrchestrator(database_service)

        # Initialize tool modules
        self.search_tools = SearchTools(database_service)
        self.note_tools = NoteTools(database_service)
        self.workflow_tools = WorkflowTools(database_service, self.workflow_orchestrator)
        self.export_tools = ExportTools(database_service)

        # Create FastMCP server
        self.mcp_server = FastMCP("BrainForge Library")

        # Register all tools
        self._register_tools()

        self.logger = logging.getLogger(__name__)

    def _register_tools(self):
        """Register all MCP tools with the server"""

        # Search and discovery tools
        self.mcp_server.tool(
            name="search_library",
            description="Search the BrainForge library using semantic search"
        )(self.search_tools.search_library)

        self.mcp_server.tool(
            name="discover_connections",
            description="Discover semantic connections between library items"
        )(self.search_tools.discover_connections)

        self.mcp_server.tool(
            name="get_library_stats",
            description="Get statistics about the BrainForge library"
        )(self.search_tools.get_library_stats)

        # Note management tools
        self.mcp_server.tool(
            name="create_note",
            description="Create a new note in the BrainForge library"
        )(self.note_tools.create_note)

        self.mcp_server.tool(
            name="update_note",
            description="Update an existing note in the BrainForge library"
        )(self.note_tools.update_note)

        self.mcp_server.tool(
            name="link_notes",
            description="Create semantic links between notes"
        )(self.note_tools.link_notes)

        # Workflow tools
        self.mcp_server.tool(
            name="start_research_workflow",
            description="Start a research workflow for agent operations"
        )(self.workflow_tools.start_research_workflow)

        self.mcp_server.tool(
            name="get_workflow_status",
            description="Get the status of a running workflow"
        )(self.workflow_tools.get_workflow_status)

        # Export tools
        self.mcp_server.tool(
            name="export_library",
            description="Export the BrainForge library in various formats"
        )(self.export_tools.export_library)

        self.mcp_server.tool(
            name="generate_documentation",
            description="Generate documentation for the library"
        )(self.export_tools.generate_documentation)

    async def create_session(self, client_info: dict[str, Any]) -> MCPSession:
        """Create a new MCP session"""
        session_create = MCPSessionCreate(
            client_info=client_info,
            status="active"
        )
        return await self.session_manager.create_session(session_create)

    async def execute_tool(
        self,
        session_id: UUID,
        tool_name: str,
        parameters: dict[str, Any]
    ) -> MCPExecution:
        """Execute an MCP tool with audit trail"""

        # Create execution record
        execution_create = MCPExecutionCreate(
            session_id=session_id,
            tool_name=tool_name,
            parameters=parameters,
            status="running"
        )

        execution = await self.session_manager.create_execution(execution_create)

        try:
            # Execute the tool
            result = await self._execute_tool_function(tool_name, parameters)

            # Update execution with result
            execution.status = "completed"
            execution.result = result
            await self.session_manager.update_execution(execution.id, execution)

            return execution

        except Exception as e:
            # Update execution with error
            execution.status = "failed"
            execution.error_message = str(e)
            await self.session_manager.update_execution(execution.id, execution)
            raise

    async def _execute_tool_function(self, tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Execute the actual tool function"""

        # Map tool names to actual functions
        tool_mapping = {
            "search_library": self.search_tools.search_library,
            "discover_connections": self.search_tools.discover_connections,
            "get_library_stats": self.search_tools.get_library_stats,
            "create_note": self.note_tools.create_note,
            "update_note": self.note_tools.update_note,
            "link_notes": self.note_tools.link_notes,
            "start_research_workflow": self.workflow_tools.start_research_workflow,
            "get_workflow_status": self.workflow_tools.get_workflow_status,
            "export_library": self.export_tools.export_library,
            "generate_documentation": self.export_tools.generate_documentation,
        }

        if tool_name not in tool_mapping:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Execute the tool function
        tool_function = tool_mapping[tool_name]
        return await tool_function(**parameters)

    async def run_server(self, host: str = "localhost", port: int = 8000):
        """Run the MCP server"""
        self.logger.info(f"Starting BrainForge MCP server on {host}:{port}")
        await self.mcp_server.run(host=host, port=port)


# Factory function for creating the MCP server
def create_mcp_server(database_url: str) -> BrainForgeMCP:
    """Create a BrainForge MCP server instance"""
    database_service = DatabaseService(database_url)
    return BrainForgeMCP(database_service)
