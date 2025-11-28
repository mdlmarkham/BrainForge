#!/usr/bin/env python3
"""Database migration script for BrainForge."""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_migration_script() -> str:
    """Create the database migration SQL script."""

    return """
-- BrainForge Database Migration Script
-- Version: 1.0.0
-- Date: 2025-11-28

-- Notes table with constitutional requirements
CREATE TABLE IF NOT EXISTS notes (
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
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    vector VECTOR(1536), -- Configurable dimension
    model_version VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Links between notes
CREATE TABLE IF NOT EXISTS links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    target_note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL CHECK (relation_type IN ('cites', 'supports', 'derived_from', 'related', 'contradicts')),
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    CHECK (source_note_id != target_note_id)
);

-- Agent run audit trails
CREATE TABLE IF NOT EXISTS agent_runs (
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
CREATE TABLE IF NOT EXISTS version_history (
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

-- Performance indexes for constitutional requirements
CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(note_type);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at);
CREATE INDEX IF NOT EXISTS idx_notes_ai_generated ON notes(is_ai_generated);
CREATE INDEX IF NOT EXISTS idx_embeddings_note_id ON embeddings(note_id);
CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_note_id);
CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_note_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_name, agent_version);
CREATE INDEX IF NOT EXISTS idx_version_history_note_version ON version_history(note_id, version);

-- Insert initial data if needed
-- INSERT INTO notes (content, note_type, created_by) VALUES ('Welcome to BrainForge!', 'permanent', 'system');
"""


def execute_migration(db_url: str, migration_sql: str) -> bool:
    """Execute the migration SQL against the database."""
    try:
        import sqlalchemy as sa
        
        # Create engine and connection
        engine = sa.create_engine(db_url)
        connection = engine.connect()
        
        # Execute the migration in a transaction
        with connection.begin() as transaction:
            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:  # Skip empty statements
                    connection.execute(sa.text(statement))
            
            transaction.commit()
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"Error executing migration: {e}")
        return False


def validate_database_connection(db_url: str) -> bool:
    """Validate database connection and permissions."""
    try:
        import sqlalchemy as sa
        
        engine = sa.create_engine(db_url)
        connection = engine.connect()
        
        # Test basic connection and permissions
        result = connection.execute(sa.text("SELECT 1"))
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"Database connection error: {e}")
        return False


def main():
    """Main migration function."""
    print("BrainForge Database Migration")
    print("=" * 40)

    # Check if we have database configuration
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your PostgreSQL connection string")
        sys.exit(1)

    # Validate database connection
    print("Validating database connection...")
    if not validate_database_connection(db_url):
        print("Failed to connect to database. Please check your DATABASE_URL and database permissions.")
        sys.exit(1)
    
    print("✓ Database connection validated")

    # Create migration script
    migration_sql = create_migration_script()

    # Execute migration
    print("Executing migration...")
    if execute_migration(db_url, migration_sql):
        print("✓ Migration completed successfully")
        return 0
    else:
        print("✗ Migration failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
