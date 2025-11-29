# Quickstart Guide: FastMCP Library Interface

**Feature**: FastMCP Library Interface (specs/004-library-mcp/spec.md)  
**Date**: 2025-11-29  
**Status**: Phase 1 Design Complete

## Overview

This guide provides implementation instructions for the FastMCP-based library interface for BrainForge. The MCP server exposes semantic-aware tools for search, note management, and linking operations while maintaining constitutional compliance.

## Prerequisites

- BrainForge core services running (PostgreSQL + PGVector, FastAPI)
- Python 3.11+ environment
- FastMCP library (`/jlowin/fastmcp`)
- SpiffWorkflow library (`/sartography/spiffworkflow`)

## Implementation Steps

### 1. Project Structure Setup

Create the MCP server module structure:

```text
src/
├── mcp/
│   ├── __init__.py
│   ├── server.py              # Main MCP server implementation
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py          # Semantic search tools
│   │   ├── notes.py           # Note management tools
│   │   ├── links.py           # Link management tools
│   │   └── export.py          # Library export tools
│   ├── auth/
│   │   ├── __init__.py
│   │   └── session.py         # Session management
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── integration.py     # SpiffWorkflow integration
│   └── models/
│       ├── __init__.py
│       ├── mcp_tool.py        # MCP tool definitions
│       ├── mcp_session.py     # Session models
│       └── mcp_execution.py   # Execution tracking
```

### 2. MCP Server Implementation

Create the main MCP server in `src/mcp/server.py`:

```python
"""BrainForge MCP Server implementation."""

from fastmcp import FastMCP
from src.services.semantic_search import SemanticSearch
from src.services.database import NoteService, LinkService
from src.compliance.constitution import ComplianceValidator
from .auth.session import SessionManager
from .workflows.integration import WorkflowOrchestrator

class BrainForgeMCP:
    """BrainForge MCP Server with constitutional compliance."""
    
    def __init__(self):
        self.mcp = FastMCP(name="BrainForgeLibrary")
        self.session_manager = SessionManager()
        self.workflow_orchestrator = WorkflowOrchestrator()
        self.compliance_validator = ComplianceValidator()
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all MCP tools with constitutional compliance."""
        
        @self.mcp.tool(tags={"search", "discovery"})
        async def semantic_search(
            query: str, 
            filters: dict = None, 
            limit: int = 10,
            session_token: str = None
        ) -> list:
            """Perform semantic search with metadata filtering."""
            # Validate session and constitutional compliance
            session = await self.session_manager.validate_session(session_token)
            compliance_result = await self.compliance_validator.validate_search(session, query, filters)
            
            if not compliance_result.approved:
                raise ValueError(f"Constitutional violation: {compliance_result.violations}")
            
            # Execute search
            search_service = SemanticSearch()
            results = await search_service.semantic_search(query, filters, limit)
            
            # Log execution for audit trail
            await self._log_tool_execution("semantic_search", session, {"query": query, "filters": filters})
            
            return results
        
        @self.mcp.tool(tags={"management", "agent"})
        async def create_note(
            content: str,
            note_type: str = "agent_generated",
            metadata: dict = None,
            ai_justification: str = None,
            session_token: str = None
        ) -> dict:
            """Create new note with constitutional compliance."""
            session = await self.session_manager.validate_session(session_token)
            compliance_result = await self.compliance_validator.validate_note_creation(
                session, content, note_type, ai_justification
            )
            
            if not compliance_result.approved:
                raise ValueError(f"Constitutional violation: {compliance_result.violations}")
            
            # Create note through workflow for human review if needed
            note_service = NoteService()
            if note_type == "agent_generated" and compliance_result.requires_review:
                workflow_result = await self.workflow_orchestrator.start_note_review_workflow(
                    session, content, metadata, ai_justification
                )
                return workflow_result
            else:
                note = await note_service.create_note(content, note_type, metadata, session.user_id)
                return {"note_id": note.id, "status": "created", "version": note.version}
    
    async def _log_tool_execution(self, tool_name: str, session, parameters: dict):
        """Log tool execution for audit trail."""
        # Implementation for execution logging
        pass
```

### 3. Authentication Integration

Implement session management in `src/mcp/auth/session.py`:

```python
"""MCP Session management with constitutional compliance."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4
from src.services.auth import AuthService

class SessionManager:
    """Manage MCP sessions with authentication and compliance."""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.active_sessions = {}
    
    async def validate_session(self, session_token: str) -> 'MCPsession':
        """Validate session token and return session object."""
        if not session_token:
            raise ValueError("Session token required")
        
        # Validate JWT token or API key
        user_info = await self.auth_service.validate_token(session_token)
        
        # Create or retrieve session
        session_id = self._get_session_id(user_info)
        if session_id not in self.active_sessions:
            session = await self._create_session(user_info)
            self.active_sessions[session_id] = session
        else:
            session = self.active_sessions[session_id]
            await self._refresh_session(session)
        
        return session
    
    async def _create_session(self, user_info: dict) -> 'MCPsession':
        """Create new MCP session."""
        return MCPsession(
            id=uuid4(),
            user_id=user_info.get('user_id'),
            agent_id=user_info.get('agent_id'),
            client_info=user_info.get('client_info', {}),
            authentication_method=user_info.get('auth_method', 'jwt'),
            constitutional_context=self._build_constitutional_context(user_info),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)
        )
```

### 4. Workflow Integration

Implement SpiffWorkflow integration in `src/mcp/workflows/integration.py`:

```python
"""SpiffWorkflow integration for MCP tool orchestration."""

from SpiffWorkflow.bpmn import BpmnWorkflow
from SpiffWorkflow.bpmn.parser import BpmnParser
from src.services.research_orchestrator import ResearchOrchestrator

class WorkflowOrchestrator:
    """Orchestrate workflows for MCP tool execution."""
    
    def __init__(self):
        self.parser = BpmnParser()
        self.research_orchestrator = ResearchOrchestrator()
    
    async def start_note_review_workflow(self, session, content, metadata, ai_justification):
        """Start human review workflow for agent-generated content."""
        workflow_def = """
        <definitions>
            <process id="agent_note_review">
                <startEvent id="start"/>
                <serviceTask id="create_note_draft" implementation="MCP_TOOL"/>
                <userTask id="human_review" name="Human Review"/>
                <exclusiveGateway id="review_decision"/>
                <serviceTask id="publish_note" implementation="MCP_TOOL"/>
                <serviceTask id="reject_note" implementation="MCP_TOOL"/>
                <endEvent id="approved"/>
                <endEvent id="rejected"/>
            </process>
        </definitions>
        """
        
        workflow = self.parser.parse_string(workflow_def)
        workflow_instance = BpmnWorkflow(workflow)
        
        # Set initial data
        workflow_instance.data = {
            'session': session.dict(),
            'content': content,
            'metadata': metadata,
            'ai_justification': ai_justification,
            'constitutional_gates': ['human_in_the_loop', 'ai_agent_integration']
        }
        
        # Start workflow
        workflow_instance.start()
        
        return {
            'workflow_instance_id': workflow_instance.id,
            'status': 'pending_review',
            'next_task': 'human_review'
        }
```

### 5. Constitutional Compliance Integration

Extend the compliance framework for MCP-specific validation:

```python
"""MCP-specific constitutional compliance validation."""

from src.compliance.constitution import ComplianceValidator, ConstitutionalPrinciple

class MCPComplianceValidator(ComplianceValidator):
    """Extended compliance validator for MCP operations."""
    
    async def validate_search(self, session, query: str, filters: dict) -> 'ComplianceResult':
        """Validate semantic search operation compliance."""
        violations = []
        
        # Check query length and content
        if len(query.strip()) < 3:
            violations.append({
                'principle': ConstitutionalPrinciple.STRUCTURED_DATA_FOUNDATION,
                'issue': 'Search query too short',
                'severity': 'medium'
            })
        
        # Check filter constraints
        if filters and 'note_type' in filters:
            valid_types = ['fleeting', 'literature', 'permanent', 'insight', 'agent_generated']
            if filters['note_type'] not in valid_types:
                violations.append({
                    'principle': ConstitutionalPrinciple.DATA_GOVERNANCE,
                    'issue': 'Invalid note type filter',
                    'severity': 'medium'
                })
        
        return ComplianceResult(
            approved=len(violations) == 0,
            violations=violations,
            requires_review=False
        )
    
    async def validate_note_creation(self, session, content: str, note_type: str, ai_justification: str):
        """Validate note creation operation compliance."""
        violations = []
        requires_review = False
        
        # Content validation
        if len(content.strip()) < 10:
            violations.append({
                'principle': ConstitutionalPrinciple.STRUCTURED_DATA_FOUNDATION,
                'issue': 'Note content too short',
                'severity': 'high'
            })
        
        # AI-generated content validation
        if note_type == 'agent_generated' and not ai_justification:
            violations.append({
                'principle': ConstitutionalPrinciple.AI_AGENT_INTEGRATION,
                'issue': 'AI-generated content requires justification',
                'severity': 'high'
            })
            requires_review = True
        
        # Human review requirement for agent content
        if note_type == 'agent_generated':
            requires_review = True
        
        return ComplianceResult(
            approved=len(violations) == 0,
            violations=violations,
            requires_review=requires_review
        )
```

## Testing Procedures

### Unit Tests

Create comprehensive unit tests for MCP tools:

```python
"""Unit tests for MCP server tools."""

import pytest
from src.mcp.tools.search import semantic_search_tool
from src.mcp.auth.session import SessionManager

class TestMCPSearchTools:
    """Test MCP search tools."""
    
    @pytest.mark.asyncio
    async def test_semantic_search_valid_query(self):
        """Test semantic search with valid query."""
        session = await SessionManager().validate_session("test_token")
        results = await semantic_search_tool("sustainable cement production", session=session)
        
        assert isinstance(results, list)
        assert len(results) <= 10  # Default limit
    
    @pytest.mark.asyncio
    async def test_semantic_search_constitutional_violation(self):
        """Test semantic search with constitutional violation."""
        session = await SessionManager().validate_session("test_token")
        
        with pytest.raises(ValueError, match="Constitutional violation"):
            await semantic_search_tool("", session=session)  # Empty query
```

### Integration Tests

Test MCP server integration with existing services:

```python
"""Integration tests for MCP server."""

import pytest
from src.mcp.server import BrainForgeMCP
from src.services.semantic_search import SemanticSearch

class TestMCPIntegration:
    """Test MCP server integration."""
    
    @pytest.mark.asyncio
    async def test_mcp_server_initialization(self):
        """Test MCP server initialization."""
        mcp_server = BrainForgeMCP()
        assert mcp_server.mcp is not None
        assert len(mcp_server.mcp.tools) > 0
    
    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Test that all required tools are registered."""
        mcp_server = BrainForgeMCP()
        tool_names = [tool.name for tool in mcp_server.mcp.tools]
        
        expected_tools = ['semantic_search', 'create_note', 'update_note', 'create_link', 'export_library']
        for tool in expected_tools:
            assert tool in tool_names
```

## Deployment Configuration

### Docker Configuration

Add MCP server to Docker Compose:

```yaml
# docker-compose.yml
version: '3.8'
services:
  brainforge-mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    ports:
      - "8081:8081"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/brainforge
      - MCP_PORT=8081
      - MCP_AUTH_REQUIRED=true
    depends_on:
      - db
      - brainforge-api
```

### Environment Variables

Configure MCP server environment:

```bash
# .env.mcp
MCP_PORT=8081
MCP_AUTH_REQUIRED=true
MCP_SESSION_TIMEOUT=86400
MCP_RATE_LIMIT_SEARCH=100
MCP_RATE_LIMIT_NOTES=50
MCP_CONSTITUTION_STRICT_MODE=true
```

## Performance Optimization

### Caching Strategy

Implement caching for frequently accessed data:

```python
"""Caching implementation for MCP tools."""

import redis
from functools import wraps

class MCPSearchCache:
    """Cache for semantic search results."""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    def cache_search_results(self, ttl=300):
        """Decorator to cache search results."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = f"search:{kwargs['query']}:{hash(str(kwargs['filters']))}"
                cached = self.redis_client.get(cache_key)
                
                if cached:
                    return json.loads(cached)
                
                result = await func(*args, **kwargs)
                self.redis_client.setex(cache_key, ttl, json.dumps(result))
                return result
            return wrapper
        return decorator
```

### Connection Pooling

Optimize database connections:

```python
"""Database connection pooling for MCP server."""

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

class MCPDatabasePool:
    """Database connection pool for MCP operations."""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600
        )
```

## Monitoring and Logging

### Audit Trail Integration

Ensure all MCP operations are logged:

```python
"""Audit trail integration for MCP tools."""

from src.models.audit_trail import AuditTrailService

class MCPAuditLogger:
    """Log MCP tool executions for audit trails."""
    
    def __init__(self):
        self.audit_service = AuditTrailService()
    
    async def log_tool_execution(self, tool_name: str, session, parameters: dict, result: dict, status: str):
        """Log tool execution to audit trail."""
        audit_entry = {
            'tool_name': tool_name,
            'session_id': session.id,
            'user_id': session.user_id,
            'agent_id': session.agent_id,
            'input_parameters': parameters,
            'output_result': result,
            'status': status,
            'execution_time_ms': result.get('execution_time', 0),
            'constitutional_compliance': result.get('compliance', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        await self.audit_service.create_audit_entry(audit_entry)
```

This quickstart guide provides the foundation for implementing the FastMCP library interface. The implementation maintains constitutional compliance while providing powerful semantic-aware tools for agent interaction with the BrainForge knowledge base.