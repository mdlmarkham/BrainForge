"""BrainForge MCP Server Main Entry Point"""

import asyncio
import logging
import os
from typing import Optional

from .server import create_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the BrainForge MCP server"""
    
    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://brainforge:brainforge@localhost:5432/brainforge"
    )
    
    # Get server configuration
    host = os.getenv("MCP_HOST", "localhost")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    logger.info(f"Starting BrainForge MCP Server")
    logger.info(f"Database: {database_url}")
    logger.info(f"Server: {host}:{port}")
    
    try:
        # Create MCP server instance
        mcp_server = create_mcp_server(database_url)
        
        # Run the server
        await mcp_server.run_server(host=host, port=port)
        
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())