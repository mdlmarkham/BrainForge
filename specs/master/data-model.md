# Data Model: Researcher Agent

**Feature**: 003-researcher-agent  
**Date**: 2025-11-29  
**Status**: Design Complete

## Core Entities

### ResearchRun
Represents a single research execution with parameters, results, and metadata.

**Fields**:
- `id`: UUID (primary key)
- `topic`: String (research topic or seed query)
- `parameters`: JSON (search parameters, quality thresholds, source preferences)
- `status`: Enum (pending, running, completed, failed)
- `started_at`: DateTime
- `completed_at`: DateTime (nullable)
- `results_count`: Integer (number of sources discovered)
- `quality_threshold`: Float (minimum score for inclusion)
- `created_by`: String (user or agent identifier)
- `created_at`: DateTime

**Relationships**:
- One-to-Many with `ContentSource` (discovered content)
- One-to-Many with `QualityAssessment` (evaluation results)

### ContentSource
External content discovered by the agent with evaluation scores and metadata.

**Fields**:
- `id`: UUID (primary key)
- `research_run_id`: UUID (foreign key to ResearchRun)
- `source_url`: String (original content URL)
- `title`: String
- `authors`: JSON array (author names and affiliations)
- `publication`: String (journal, website, publisher)
- `publication_date`: Date
- `content_type`: Enum (article, paper, report, blog, news)
- `language`: String (ISO code)
- `license_info`: String (copyright/license information)
- `summary`: Text (AI-generated summary)
- `key_points`: JSON array (extracted insights)
- `raw_metadata`: JSON (original API response data)
- `discovered_at`: DateTime

**Relationships**:
- Many-to-One with `ResearchRun`
- One-to-One with `QualityAssessment`
- One-to-Many with `IntegrationProposal`

### QualityAssessment
Multi-factor evaluation of content credibility, relevance, and quality.

**Fields**:
- `id`: UUID (primary key)
- `content_source_id`: UUID (foreign key to ContentSource)
- `credibility_score`: Float (0.0-1.0)
- `relevance_score`: Float (0.0-1.0)
- `freshness_score`: Float (0.0-1.0)
- `completeness_score`: Float (0.0-1.0)
- `overall_score`: Float (weighted average)
- `confidence_level`: Enum (high, medium, low)
- `evaluation_rationale`: Text (AI explanation of scores)
- `red_flags`: JSON array (potential issues identified)
- `evaluated_at`: DateTime
- `evaluated_by`: String (agent identifier and version)

**Validation Rules**:
- Overall score = (credibility * 0.4) + (relevance * 0.3) + (freshness * 0.15) + (completeness * 0.15)
- Scores must be between 0.0 and 1.0
- Confidence level auto-assigned based on score variance

### ReviewQueue
Collection of agent-proposed content awaiting human decision.

**Fields**:
- `id`: UUID (primary key)
- `content_source_id`: UUID (foreign key to ContentSource)
- `status`: Enum (pending, approved, rejected, modified)
- `priority`: Enum (high, medium, low) - based on quality score
- `assigned_to`: String (reviewer identifier, nullable)
- `submitted_at`: DateTime
- `reviewed_at`: DateTime (nullable)
- `review_decision`: Enum (approve, reject, modify)
- `review_notes`: Text (human reviewer comments)
- `modifications`: JSON (content modifications made by reviewer)

**State Transitions**:
- pending → approved/rejected/modified (after human review)
- approved → integrated (moves to ingestion pipeline)
- modified → pending (returns for re-evaluation)

### IntegrationProposal
Suggested connections and classifications for new content within existing knowledge.

**Fields**:
- `id`: UUID (primary key)
- `content_source_id`: UUID (foreign key to ContentSource)
- `target_note_ids`: JSON array (UUIDs of existing notes for connection)
- `suggested_tags`: JSON array (classification tags)
- `connection_strength`: Float (semantic similarity score)
- `integration_rationale`: Text (AI explanation of connections)
- `suggested_actions`: JSON array (create new note, enhance existing, link reference)
- `generated_at`: DateTime

**Validation Rules**:
- Connection strength must be >= 0.0
- At least one target note or suggested tag required

### AuditTrail
Complete record of discovery, evaluation, and decision processes.

**Fields**:
- `id`: UUID (primary key)
- `research_run_id`: UUID (foreign key to ResearchRun)
- `action_type`: Enum (discovery, evaluation, review, integration)
- `entity_type`: String (ResearchRun, ContentSource, etc.)
- `entity_id`: UUID
- `action_details`: JSON (parameters, results, changes)
- `performed_by`: String (user or agent identifier)
- `performed_at`: DateTime
- `version_info`: String (agent version, system version)

## Database Schema Extensions

### New Tables
```sql
-- ResearchRun table
CREATE TABLE research_run (
    id UUID PRIMARY KEY,
    topic TEXT NOT NULL,
    parameters JSONB,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results_count INTEGER DEFAULT 0,
    quality_threshold FLOAT DEFAULT 0.5,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ContentSource table  
CREATE TABLE content_source (
    id UUID PRIMARY KEY,
    research_run_id UUID REFERENCES research_run(id),
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    authors JSONB,
    publication TEXT,
    publication_date DATE,
    content_type TEXT CHECK (content_type IN ('article', 'paper', 'report', 'blog', 'news')),
    language TEXT DEFAULT 'en',
    license_info TEXT,
    summary TEXT,
    key_points JSONB,
    raw_metadata JSONB,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- QualityAssessment table
CREATE TABLE quality_assessment (
    id UUID PRIMARY KEY,
    content_source_id UUID REFERENCES content_source(id) UNIQUE,
    credibility_score FLOAT CHECK (credibility_score >= 0.0 AND credibility_score <= 1.0),
    relevance_score FLOAT CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
    freshness_score FLOAT CHECK (freshness_score >= 0.0 AND freshness_score <= 1.0),
    completeness_score FLOAT CHECK (completeness_score >= 0.0 AND completeness_score <= 1.0),
    overall_score FLOAT GENERATED ALWAYS AS (
        (credibility_score * 0.4) + 
        (relevance_score * 0.3) + 
        (freshness_score * 0.15) + 
        (completeness_score * 0.15)
    ) STORED,
    confidence_level TEXT CHECK (confidence_level IN ('high', 'medium', 'low')),
    evaluation_rationale TEXT,
    red_flags JSONB,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evaluated_by TEXT NOT NULL
);

-- ReviewQueue table
CREATE TABLE review_queue (
    id UUID PRIMARY KEY,
    content_source_id UUID REFERENCES content_source(id) UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected', 'modified')),
    priority TEXT CHECK (priority IN ('high', 'medium', 'low')),
    assigned_to TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_decision TEXT CHECK (review_decision IN ('approve', 'reject', 'modify')),
    review_notes TEXT,
    modifications JSONB
);

-- IntegrationProposal table
CREATE TABLE integration_proposal (
    id UUID PRIMARY KEY,
    content_source_id UUID REFERENCES content_source(id),
    target_note_ids JSONB,
    suggested_tags JSONB,
    connection_strength FLOAT CHECK (connection_strength >= 0.0),
    integration_rationale TEXT,
    suggested_actions JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AuditTrail table (extends existing audit infrastructure)
CREATE TABLE research_audit_trail (
    id UUID PRIMARY KEY,
    research_run_id UUID REFERENCES research_run(id),
    action_type TEXT NOT NULL CHECK (action_type IN ('discovery', 'evaluation', 'review', 'integration')),
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    action_details JSONB,
    performed_by TEXT NOT NULL,
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version_info TEXT NOT NULL
);
```

## Indexes for Performance
```sql
CREATE INDEX idx_research_run_status ON research_run(status);
CREATE INDEX idx_research_run_created_at ON research_run(created_at);
CREATE INDEX idx_content_source_research_run ON content_source(research_run_id);
CREATE INDEX idx_content_source_discovered_at ON content_source(discovered_at);
CREATE INDEX idx_quality_assessment_score ON quality_assessment(overall_score);
CREATE INDEX idx_review_queue_status ON review_queue(status);
CREATE INDEX idx_review_queue_priority ON review_queue(priority);
CREATE INDEX idx_audit_trail_research_run ON research_audit_trail(research_run_id);
CREATE INDEX idx_audit_trail_entity ON research_audit_trail(entity_type, entity_id);
```

## Data Integrity Constraints

- Foreign key constraints ensure relational integrity
- Check constraints enforce domain-specific validation
- Generated columns maintain calculated values
- Unique constraints prevent duplicates
- JSONB fields provide flexibility for complex data structures

This data model supports all functional requirements while maintaining constitutional compliance through complete auditability and structured data foundation.