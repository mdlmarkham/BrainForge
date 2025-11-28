# Data Model: AI Knowledge Base

**Feature**: AI Knowledge Base  
**Date**: 2025-11-28  
**Plan**: [plan.md](plan.md)  
**Research**: [research.md](research.md)

## Core Entities

### Note
Primary unit of knowledge with versioning and provenance tracking.

**Fields**:
- `id`: UUID (primary key)
- `content`: Text (markdown supported)
- `note_type`: Enum (fleeting, literature, permanent, insight, agent_generated)
- `metadata`: JSONB (tags, custom fields)
- `provenance`: JSONB (source information, creation method)
- `version`: Integer (optimistic locking)
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `created_by`: String (user or agent identifier)
- `is_ai_generated`: Boolean (constitutional requirement)
- `ai_justification`: Text (rationale for AI-generated content)

**Relationships**:
- One-to-many: Note → Embedding (vector representations)
- One-to-many: Note → Link (outgoing relationships)
- One-to-many: Note → Link (incoming relationships)
- One-to-many: Note → VersionHistory

**Validation Rules**:
- Content must be non-empty
- Note type must be valid enum value
- AI-generated content must include justification
- Version must increment on updates

### Embedding
Vector representation of note content for semantic search.

**Fields**:
- `id`: UUID (primary key)
- `note_id`: UUID (foreign key to Note)
- `vector`: Vector (PGVector type, dimension configurable)
- `model_version`: String (embedding model identifier)
- `created_at`: Timestamp

**Relationships**:
- Many-to-one: Embedding → Note

**Validation Rules**:
- Vector dimension must match configured model
- Model version must be tracked for compatibility

### Link
Explicit relationships between notes with typed connections.

**Fields**:
- `id`: UUID (primary key)
- `source_note_id`: UUID (foreign key to Note)
- `target_note_id`: UUID (foreign key to Note)
- `relation_type`: Enum (cites, supports, derived_from, related, contradicts)
- `created_at`: Timestamp
- `created_by`: String (user or agent identifier)

**Relationships**:
- Many-to-one: Link → Note (as source)
- Many-to-one: Link → Note (as target)

**Validation Rules**:
- Source and target notes must exist
- Relation type must be valid enum value
- No self-referential links allowed

### AgentRun
Audit trail for AI agent operations with constitutional compliance.

**Fields**:
- `id`: UUID (primary key)
- `agent_name`: String (agent identifier)
- `agent_version`: String (constitutional versioning requirement)
- `input_parameters`: JSONB (agent input data)
- `output_note_ids`: Array[UUID] (created or modified notes)
- `status`: Enum (success, failed, pending_review)
- `started_at`: Timestamp
- `completed_at`: Timestamp
- `error_details`: Text (if failed)
- `human_reviewer`: String (if reviewed)
- `reviewed_at`: Timestamp
- `review_status`: Enum (approved, rejected, needs_revision)

**Relationships**:
- One-to-many: AgentRun → Note (through output_note_ids)

**Validation Rules**:
- Agent version must be specified
- Status transitions must follow constitutional workflow
- Human review required for final status of agent outputs

### VersionHistory
Complete change tracking for constitutional auditability.

**Fields**:
- `id`: UUID (primary key)
- `note_id`: UUID (foreign key to Note)
- `version`: Integer
- `content`: Text
- `metadata`: JSONB
- `changes`: JSONB (diff information)
- `created_at`: Timestamp
- `created_by`: String (user or agent identifier)
- `change_reason`: Text (optional explanation)

**Relationships**:
- Many-to-one: VersionHistory → Note

**Validation Rules**:
- Version must be sequential
- Changes must be recorded for audit purposes

## Database Schema

### Tables
```sql
-- Notes table with constitutional requirements
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    note_type VARCHAR(50) NOT NULL CHECK (note_type IN ('fleeting', 'literature', 'permanent', 'insight', 'agent_generated')),
    metadata JSONB DEFAULT '{}',
    provenance JSONB DEFAULT '{}',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    ai_justification TEXT,
    CHECK (NOT (is_ai_generated AND ai_justification IS NULL))
);

-- Embeddings for semantic search
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    vector VECTOR(1536), -- Configurable dimension
    model_version VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Links between notes
CREATE TABLE links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    target_note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL CHECK (relation_type IN ('cites', 'supports', 'derived_from', 'related', 'contradicts')),
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    CHECK (source_note_id != target_note_id)
);

-- Agent run audit trails
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(255) NOT NULL,
    agent_version VARCHAR(100) NOT NULL,
    input_parameters JSONB DEFAULT '{}',
    output_note_ids UUID[] DEFAULT '{}',
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'failed', 'pending_review')),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_details TEXT,
    human_reviewer VARCHAR(255),
    reviewed_at TIMESTAMP,
    review_status VARCHAR(50) CHECK (review_status IN ('approved', 'rejected', 'needs_revision'))
);

-- Version history for constitutional auditability
CREATE TABLE version_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    changes JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    change_reason TEXT
);
```

### Indexes for Performance
```sql
-- Performance indexes for constitutional requirements
CREATE INDEX idx_notes_type ON notes(note_type);
CREATE INDEX idx_notes_created_at ON notes(created_at);
CREATE INDEX idx_notes_ai_generated ON notes(is_ai_generated);
CREATE INDEX idx_embeddings_note_id ON embeddings(note_id);
CREATE INDEX idx_links_source ON links(source_note_id);
CREATE INDEX idx_links_target ON links(target_note_id);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
CREATE INDEX idx_agent_runs_agent ON agent_runs(agent_name, agent_version);
CREATE INDEX idx_version_history_note_version ON version_history(note_id, version);
```

## Pydantic Models

### Note Model
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class NoteType(str, Enum):
    FLEETING = "fleeting"
    LITERATURE = "literature" 
    PERMANENT = "permanent"
    INSIGHT = "insight"
    AGENT_GENERATED = "agent_generated"

class NoteBase(BaseModel):
    content: str = Field(..., min_length=1)
    note_type: NoteType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

class NoteCreate(NoteBase):
    created_by: str
    is_ai_generated: bool = False
    ai_justification: Optional[str] = None

class Note(NoteBase):
    id: str
    version: int
    created_at: str
    updated_at: str
    created_by: str
    is_ai_generated: bool
    ai_justification: Optional[str]
    
    class Config:
        from_attributes = True
```

## Constitutional Compliance

This data model fully complies with BrainForge Constitution requirements:

1. **Structured Data Foundation**: Clear entity definitions with explicit boundaries
2. **Versioning & Auditability**: Complete change tracking through VersionHistory
3. **AI Agent Integration**: AgentRun table with audit trails and versioning
4. **Human-in-the-Loop**: Review status and human reviewer fields
5. **Data Governance**: Provenance tracking and metadata validation
6. **Error Handling**: Status tracking and error details for recovery

The model supports all functional requirements from the specification while maintaining constitutional principles.