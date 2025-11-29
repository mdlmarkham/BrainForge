# Research Findings: FastMCP Library Interface

**Feature**: FastMCP Library Interface (specs/004-library-mcp/spec.md)  
**Date**: 2025-11-29  
**Phase**: 0 - Research and Planning

## Executive Summary

This research phase identified and resolved key unknowns for implementing a FastMCP-based library interface for BrainForge. The research focused on FastMCP integration patterns, SpiffWorkflow orchestration, MCP server implementation, and semantic search integration while maintaining constitutional compliance.

## Technical Context Analysis

### Current Project State
- **Language/Version**: Python 3.11+ (constitution requirement)
- **Primary Dependencies**: FastAPI, PostgreSQL/PGVector, PydanticAI, SQLAlchemy
- **Storage**: PostgreSQL with PGVector extension for vector storage
- **Testing**: pytest with contract/integration/unit test structure
- **Target Platform**: Linux server with FastAPI backend
- **Project Type**: Single project with src/tests structure
- **Performance Goals**: 2-second semantic search response, 100 concurrent agent operations
- **Constraints**: Constitutional compliance, audit trails, human review gates
- **Scale/Scope**: Multi-tenant agent operations with semantic knowledge base

### Existing Infrastructure
- Semantic search pipeline with vector similarity and metadata filtering
- Note management system with version history and audit trails
- Agent run tracking and workflow execution
- Constitutional compliance framework with validation middleware

## Research Decisions

### FastMCP Implementation Strategy

**Decision**: Use `/jlowin/fastmcp` library for MCP server implementation

**Rationale**:
- Highest benchmark score (82.4) among FastMCP implementations
- Comprehensive code snippet coverage (1375 examples)
- High source reputation with proven production usage
- Supports both HTTP and stdio transport modes
- Includes OpenAPI integration capabilities
- Provides stateless request building for performance

**Alternatives considered**:
- `/stevens507/fastmcp`: Lower code coverage (38 snippets)
- `/punkpeye/fastmcp`: TypeScript implementation, not Python
- `/websites/gofastmcp`: Lower benchmark score (53.5)

### SpiffWorkflow Integration

**Decision**: Use `/sartography/spiffworkflow` for agent workflow orchestration

**Rationale**:
- High source reputation with extensive BPMN support
- Comprehensive workflow patterns and task management
- Callback system for constitutional compliance integration
- SQLite/PostgreSQL serialization capabilities
- Manual and automated task handling

**Alternatives considered**:
- Apache Airflow: Overly complex for agent workflows
- Custom workflow engine: Would violate constitution's "Progressive Enhancement" principle

### MCP Server Architecture

**Decision**: Implement dedicated MCP server with tool/resource abstraction

**Rationale**:
- Separates library interface from core API for security
- Enables tool composition and recursive tag filtering
- Supports both agent and human interaction patterns
- Maintains constitutional audit trails through callbacks

**Alternatives considered**:
- Direct API exposure: Would bypass constitutional compliance gates
- Plugin architecture: Too complex for initial implementation

### Semantic Search Integration

**Decision**: Expose semantic search as MCP tools with metadata filtering

**Rationale**:
- Leverages existing vector store and HNSW index
- Maintains performance goals (2-second response time)
- Supports constitutional requirements through existing audit trails
- Enables progressive enhancement without AI dependencies

## Constitution Compliance Analysis

### Gates Evaluation

| Principle | Status | Justification |
|-----------|--------|---------------|
| Structured Data Foundation | PASS | Existing note/link models with versioning |
| AI Agent Integration | PASS | Agent run tracking and audit trails implemented |
| Versioning & Auditability | PASS | Version history and provenance mixins available |
| Test-First Development | PASS | Existing test structure with contract tests |
| Progressive Enhancement | PASS | Core search works without AI dependencies |
| Roles & Permissions | NEEDS IMPLEMENTATION | MCP server requires authentication integration |
| Data Governance | PASS | External content validation through existing services |
| Error Handling | PASS | FastAPI middleware with compliance validation |
| AI Versioning | PASS | Agent version tracking in run models |
| Human-in-the-Loop | PASS | Review queues and approval workflows exist |

### Compliance Violations

**GATE VIOLATION**: Roles & Permissions principle requires MCP server authentication

**Justification**: The MCP server implementation must integrate with existing authentication system to maintain constitutional compliance. This is a required enhancement for Phase 1 design.

## Implementation Architecture

### MCP Server Structure
```python
from fastmcp import FastMCP
from src.services.semantic_search import SemanticSearch
from src.services.database import NoteService

mcp = FastMCP(name="BrainForgeLibrary")

@mcp.tool(tags={"search", "discovery"})
async def semantic_search(query: str, filters: dict = None) -> list:
    """Perform semantic search with metadata filtering."""
    # Integrate with existing semantic search service
    # Maintain constitutional audit trails
    pass

@mcp.tool(tags={"management", "agent"})
async def create_note(content: str, metadata: dict) -> dict:
    """Create new note with constitutional compliance."""
    # Use existing note service with versioning
    # Trigger human review workflow if needed
    pass
```

### Workflow Integration
```python
from SpiffWorkflow.bpmn import BpmnWorkflow
from SpiffWorkflow.bpmn.parser import BpmnParser

# BPMN workflow for agent content creation with human review
workflow_spec = """
<definitions>
    <process id="agent_content_creation">
        <startEvent id="start"/>
        <serviceTask id="create_note" implementation="MCP_TOOL"/>
        <exclusiveGateway id="review_decision"/>
        <userTask id="human_review" name="Human Review"/>
        <endEvent id="approved"/>
        <endEvent id="rejected"/>
    </process>
</definitions>
"""
```

## Key Research Findings

### FastMCP Capabilities
- **Tool Composition**: Supports recursive tag filtering for environment-specific tools
- **Resource Management**: Static and dynamic resources for configuration and data
- **Transport Flexibility**: HTTP and stdio modes for different deployment scenarios
- **Performance**: Stateless request building with sub-10ms initialization

### SpiffWorkflow Integration Points
- **Callback System**: Hook into task lifecycle for constitutional compliance
- **Manual Task Handling**: Support human-in-the-loop review processes
- **BPMN Support**: Standard workflow definition for agent operations
- **Error Recovery**: Built-in error handling and task state management

### Constitutional Requirements
- **Audit Trails**: MCP tools must log operations through existing compliance framework
- **Version Control**: Note operations must use existing versioning system
- **Human Review**: Agent content creation must trigger review workflows
- **Error Handling**: MCP server must integrate with FastAPI error middleware

## Next Steps for Phase 1 Design

1. **MCP Server Implementation**: Create dedicated server with tool/resource abstraction
2. **Authentication Integration**: Connect MCP server to existing auth system
3. **Workflow Definition**: Design BPMN workflows for agent operations
4. **Constitutional Integration**: Ensure all MCP tools maintain compliance
5. **Performance Testing**: Validate 2-second search response under load

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| MCP authentication bypass | High | Integrate with existing auth middleware |
| Performance degradation | Medium | Use stateless request building patterns |
| Constitutional compliance gaps | High | Implement callback-based audit trails |
| Workflow orchestration complexity | Medium | Start with simple BPMN definitions |

## Conclusion

The research phase successfully resolved all key unknowns and identified a viable implementation strategy using FastMCP and SpiffWorkflow. The architecture maintains constitutional compliance while providing the required library interface capabilities. Phase 1 design can proceed with confidence in the technical approach.