# API Contracts: FastMCP Library Interface

**Feature**: FastMCP Library Interface (specs/004-library-mcp/spec.md)  
**Date**: 2025-11-29  
**Status**: Phase 1 Design Complete

## MCP Tool Specifications

### Core MCP Tools

#### Semantic Search Tool

**Tool Name**: `semantic_search`  
**Description**: Perform semantic search with metadata filtering  
**Tags**: `search`, `discovery`  
**Authentication Required**: Yes  
**Constitutional Gates**: `structured_data_foundation`, `data_governance`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "description": "Search query text"
    },
    "filters": {
      "type": "object",
      "properties": {
        "note_type": {
          "type": "string",
          "enum": ["fleeting", "literature", "permanent", "insight", "agent_generated"]
        },
        "tags": {
          "type": "array",
          "items": {"type": "string"},
          "maxItems": 10
        },
        "created_after": {
          "type": "string",
          "format": "date-time"
        },
        "created_before": {
          "type": "string",
          "format": "date-time"
        }
      }
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 10
    },
    "include_excerpts": {
      "type": "boolean",
      "default": true
    }
  },
  "required": ["query"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "note_id": {"type": "string", "format": "uuid"},
          "similarity_score": {"type": "number", "minimum": 0, "maximum": 1},
          "metadata": {
            "type": "object",
            "properties": {
              "title": {"type": "string"},
              "note_type": {"type": "string"},
              "tags": {"type": "array", "items": {"type": "string"}},
              "created_at": {"type": "string", "format": "date-time"}
            }
          },
          "excerpt": {"type": "string", "maxLength": 500}
        }
      }
    },
    "total_results": {"type": "integer"},
    "search_time_ms": {"type": "integer"}
  }
}
```

#### Note Creation Tool

**Tool Name**: `create_note`  
**Description**: Create new note with constitutional compliance  
**Tags**: `management`, `agent`  
**Authentication Required**: Yes  
**Constitutional Gates**: `human_in_the_loop`, `ai_agent_integration`, `versioning_auditability`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "content": {
      "type": "string",
      "minLength": 10,
      "description": "Note content (markdown supported)"
    },
    "note_type": {
      "type": "string",
      "enum": ["fleeting", "literature", "permanent", "insight", "agent_generated"],
      "default": "agent_generated"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "tags": {
          "type": "array",
          "items": {"type": "string"},
          "maxItems": 10
        },
        "source": {"type": "string"}
      }
    },
    "ai_justification": {
      "type": "string",
      "description": "Required for AI-generated content"
    }
  },
  "required": ["content"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "note_id": {"type": "string", "format": "uuid"},
    "version": {"type": "integer"},
    "status": {
      "type": "string",
      "enum": ["created", "pending_review", "rejected"]
    },
    "review_workflow_id": {"type": "string", "format": "uuid"},
    "created_at": {"type": "string", "format": "date-time"}
  }
}
```

#### Note Update Tool

**Tool Name**: `update_note`  
**Description**: Update existing note with version history preservation  
**Tags**: `management`, `agent`  
**Authentication Required**: Yes  
**Constitutional Gates**: `versioning_auditability`, `human_in_the_loop`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "note_id": {
      "type": "string",
      "format": "uuid",
      "description": "ID of note to update"
    },
    "content": {
      "type": "string",
      "minLength": 10,
      "description": "Updated note content"
    },
    "metadata": {
      "type": "object",
      "description": "Updated metadata"
    },
    "change_reason": {
      "type": "string",
      "description": "Reason for the update"
    },
    "version": {
      "type": "integer",
      "minimum": 1,
      "description": "Current version for optimistic locking"
    }
  },
  "required": ["note_id", "content", "version"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "note_id": {"type": "string", "format": "uuid"},
    "new_version": {"type": "integer"},
    "previous_version": {"type": "integer"},
    "status": {
      "type": "string",
      "enum": ["updated", "pending_review", "rejected"]
    },
    "updated_at": {"type": "string", "format": "date-time"}
  }
}
```

#### Link Creation Tool

**Tool Name**: `create_link`  
**Description**: Establish semantic relationship between notes  
**Tags**: `management`, `relationships`  
**Authentication Required**: Yes  
**Constitutional Gates**: `structured_data_foundation`, `data_governance`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "source_note_id": {
      "type": "string",
      "format": "uuid",
      "description": "Source note ID"
    },
    "target_note_id": {
      "type": "string",
      "format": "uuid",
      "description": "Target note ID"
    },
    "relation_type": {
      "type": "string",
      "enum": ["cites", "supports", "derived_from", "related", "contradicts"]
    },
    "metadata": {
      "type": "object",
      "description": "Link metadata"
    }
  },
  "required": ["source_note_id", "target_note_id", "relation_type"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "link_id": {"type": "string", "format": "uuid"},
    "source_note_id": {"type": "string", "format": "uuid"},
    "target_note_id": {"type": "string", "format": "uuid"},
    "relation_type": {"type": "string"},
    "created_at": {"type": "string", "format": "date-time"}
  }
}
```

#### Library Export Tool

**Tool Name**: `export_library`  
**Description**: Export library subset in portable format  
**Tags**: `export`, `navigation`  
**Authentication Required**: Yes  
**Constitutional Gates**: `data_governance`, `roles_permissions`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "format": {
      "type": "string",
      "enum": ["json", "markdown", "obsidian"],
      "default": "json"
    },
    "filters": {
      "type": "object",
      "properties": {
        "note_ids": {
          "type": "array",
          "items": {"type": "string", "format": "uuid"},
          "maxItems": 100
        },
        "tags": {
          "type": "array",
          "items": {"type": "string"},
          "maxItems": 10
        },
        "note_type": {
          "type": "string",
          "enum": ["fleeting", "literature", "permanent", "insight", "agent_generated"]
        }
      }
    },
    "include_content": {
      "type": "boolean",
      "default": true
    },
    "include_links": {
      "type": "boolean",
      "default": true
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "export_id": {"type": "string", "format": "uuid"},
    "format": {"type": "string"},
    "note_count": {"type": "integer"},
    "link_count": {"type": "integer"},
    "file_size_bytes": {"type": "integer"},
    "download_url": {"type": "string", "format": "uri"},
    "expires_at": {"type": "string", "format": "date-time"}
  }
}
```

## MCP Server API Endpoints

### Authentication Endpoints

#### Initialize Session
- **Endpoint**: `POST /mcp/sessions`
- **Description**: Initialize MCP server session with authentication
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Session ID and available tools

#### Refresh Session
- **Endpoint**: `PUT /mcp/sessions/{session_id}`
- **Description**: Refresh session activity and extend expiration
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Updated session information

#### Terminate Session
- **Endpoint**: `DELETE /mcp/sessions/{session_id}`
- **Description**: Terminate MCP server session
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Session termination confirmation

### Tool Execution Endpoints

#### List Available Tools
- **Endpoint**: `GET /mcp/tools`
- **Description**: List all available MCP tools with metadata
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Array of tool definitions

#### Execute Tool
- **Endpoint**: `POST /mcp/tools/{tool_name}/execute`
- **Description**: Execute specific MCP tool with parameters
- **Headers**: `Authorization: Bearer <token>`
- **Body**: Tool-specific input parameters
- **Response**: Tool execution result

#### Get Tool Execution Status
- **Endpoint**: `GET /mcp/executions/{execution_id}`
- **Description**: Get status and result of tool execution
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Execution status and result

### Workflow Integration Endpoints

#### List Available Workflows
- **Endpoint**: `GET /mcp/workflows`
- **Description**: List available SpiffWorkflow definitions
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Array of workflow definitions

#### Start Workflow
- **Endpoint**: `POST /mcp/workflows/{workflow_id}/start`
- **Description**: Start workflow execution with initial parameters
- **Headers**: `Authorization: Bearer <token>`
- **Body**: Workflow initialization parameters
- **Response**: Workflow instance ID

#### Get Workflow Status
- **Endpoint**: `GET /mcp/workflows/instances/{instance_id}`
- **Description**: Get workflow execution status and current state
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Workflow status and task information

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object",
    "constitutional_violations": "array"
  }
}
```

### Common Error Codes
- `MCP_AUTH_REQUIRED`: Authentication required but not provided
- `MCP_TOOL_NOT_FOUND`: Requested tool does not exist
- `MCP_INVALID_INPUT`: Tool input validation failed
- `MCP_CONSTITUTION_VIOLATION`: Constitutional compliance gate failed
- `MCP_SESSION_EXPIRED`: MCP session has expired
- `MCP_RATE_LIMIT_EXCEEDED`: Rate limit exceeded for tool execution

## Rate Limiting

### Tool Execution Limits
- **Semantic Search**: 100 requests per minute per session
- **Note Operations**: 50 requests per minute per session  
- **Link Operations**: 30 requests per minute per session
- **Export Operations**: 10 requests per hour per session

### Session Limits
- **Maximum Concurrent Sessions**: 10 per user/agent
- **Session Duration**: 24 hours maximum
- **Inactivity Timeout**: 1 hour of inactivity

## Constitutional Compliance Integration

All API endpoints integrate with the BrainForge constitutional compliance framework:

1. **Pre-execution validation**: Input parameters validated against constitutional gates
2. **Execution monitoring**: Real-time compliance monitoring during tool execution
3. **Post-execution audit**: Comprehensive audit trail with compliance verification
4. **Error handling**: Constitutional violations result in appropriate error responses

The MCP server maintains full audit trails for all tool executions, including constitutional compliance verification results and any gate violations.