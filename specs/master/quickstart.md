# Quickstart Guide: BrainForge AI Knowledge Base

**Feature**: AI Knowledge Base  
**Date**: 2025-11-28  
**Plan**: [plan.md](plan.md)  
**Data Model**: [data-model.md](data-model.md)  
**API**: [contracts/openapi.yaml](contracts/openapi.yaml)

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ with PGVector extension
- Docker (for containerized deployment)

## Setup Instructions

### 1. Database Setup
```bash
# Install PostgreSQL with PGVector
# Create database and enable extension
createdb brainforge
psql brainforge -c "CREATE EXTENSION vector;"
```

### 2. Project Setup
```bash
# Clone and setup project
git clone <repository> brainforge
cd brainforge
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration
Create `config/database.env`:
```env
DATABASE_URL=postgresql://user:password@localhost/brainforge
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

### 4. Initialize Database
```bash
# Run migrations
python src/cli/migrate.py
```

## Basic Usage

### Creating Notes
```python
from src.models.note import NoteCreate, NoteType
from src.services.note_service import NoteService

note_service = NoteService()

# Create a human-authored note
note = note_service.create_note(NoteCreate(
    content="This is a research note about AI knowledge management",
    note_type=NoteType.LITERATURE,
    created_by="user@example.com",
    metadata={"tags": ["research", "ai"]}
))

print(f"Created note: {note.id}")
```

### Semantic Search
```python
from src.services.search_service import SearchService

search_service = SearchService()

# Hybrid search (metadata + semantic)
results = search_service.hybrid_search(
    semantic_query="AI knowledge management systems",
    filters={"note_type": "literature"},
    limit=10
)

for note in results.notes:
    print(f"{note.id}: {note.content[:100]}...")
```

### AI Agent Workflow
```python
from src.services.agent_service import AgentService

agent_service = AgentService()

# Run research agent
run = agent_service.execute_agent(
    agent_name="research_agent",
    agent_version="1.0.0",
    input_parameters={
        "topic": "AI knowledge management",
        "depth": "comprehensive"
    }
)

# Check status and review if needed
if run.status == "pending_review":
    agent_service.submit_review(
        run_id=run.id,
        reviewer="user@example.com",
        review_status="approved"
    )
```

## API Usage

### REST API
Start the server:
```bash
uvicorn src.api.main:app --reload --port 8000
```

Example API calls:
```bash
# Create note
curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test note content",
    "note_type": "fleeting",
    "created_by": "test@example.com"
  }'

# Search notes
curl "http://localhost:8000/notes?semantic_query=knowledge%20management&limit=5"
```

### MCP Server Integration
The system exposes MCP servers for AI tool integration:

```python
# Connect to BrainForge MCP server
from fastmcp import FastMCP

mcp = FastMCP("brainforge")
result = mcp.search_notes(query="AI research", limit=10)
```

## Constitutional Compliance Features

### Audit Trails
All operations are logged with complete audit trails:
```python
# View agent run history
runs = agent_service.get_agent_runs(agent_name="research_agent")
for run in runs:
    print(f"Run {run.id}: {run.status} by {run.agent_version}")
```

### Version History
```python
# View note version history
versions = note_service.get_version_history(note_id=note.id)
for version in versions:
    print(f"Version {version.version}: {version.created_by}")
```

### Human Review Workflow
```python
# Get pending reviews
pending = agent_service.get_pending_reviews()
for run in pending:
    # Human reviews required for constitutional compliance
    agent_service.submit_review(
        run_id=run.id,
        reviewer="human@example.com",
        review_status="approved",
        review_notes="Content looks accurate and relevant"
    )
```

## Testing

### Run Tests
```bash
# Unit tests
pytest tests/unit/

# Contract tests for AI interfaces
pytest tests/contract/

# Integration tests
pytest tests/integration/

# Performance benchmarks
pytest tests/performance/
```

### Contract Testing
```python
# Example contract test for agent interface
def test_agent_contract():
    # Verify agent input/output contracts
    result = agent_service.execute_agent(
        agent_name="test_agent",
        agent_version="1.0.0",
        input_parameters={"test": "data"}
    )
    assert result.agent_version == "1.0.0"
    assert "output_note_ids" in result.dict()
```

## Deployment

### Docker Deployment
```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Production Configuration
Create `config/production.env`:
```env
DATABASE_URL=postgresql://prod_user:password@db.prod.com/brainforge
EMBEDDING_MODEL=text-embedding-3-large
LOG_LEVEL=INFO
```

## Troubleshooting

### Common Issues

**Database Connection**:
```bash
# Test connection
python src/cli/test_connection.py
```

**Vector Search Performance**:
```bash
# Reindex embeddings
python src/cli/reindex_embeddings.py
```

**Agent Workflow Errors**:
```bash
# Check agent logs
docker-compose logs agents
```

### Monitoring
- API health: `http://localhost:8000/health`
- Agent status: `http://localhost:8000/agent/status`
- Database metrics: PostgreSQL monitoring tools

## Next Steps

- Review [data-model.md](data-model.md) for detailed entity definitions
- Explore [API documentation](contracts/openapi.yaml) for complete endpoint details
- Check [constitutional compliance](../1-ai-knowledge-base/checklists/constitution-compliance.md) for governance requirements
- Implement custom agents using the MCP server framework

This quickstart provides the foundation for building constitutional-compliant AI knowledge management systems.