"""Initial migration for BrainForge database.

Revision ID: 001_initial_migration
Revises: 
Create Date: 2025-11-28 20:00:00.000000

"""
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create enum types (check if they exist first to avoid duplicates)
    # Note: PostgreSQL doesn't support CREATE TYPE IF NOT EXISTS for enums
    # We'll use a try-catch approach by checking if the type exists in pg_type
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'note_type') THEN
                CREATE TYPE note_type AS ENUM (
                    'fleeting', 'literature', 'permanent', 'insight', 'agent_generated'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'relation_type') THEN
                CREATE TYPE relation_type AS ENUM (
                    'cites', 'supports', 'derived_from', 'related', 'contradicts'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agent_run_status') THEN
                CREATE TYPE agent_run_status AS ENUM (
                    'success', 'failed', 'pending_review'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'review_status') THEN
                CREATE TYPE review_status AS ENUM (
                    'approved', 'rejected', 'needs_revision'
                );
            END IF;
        END $$;
    """)

    # Create tables using raw SQL to avoid SQLAlchemy enum creation issues
    op.execute("""
        CREATE TABLE notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            created_by VARCHAR(255) NOT NULL,
            provenance JSON NOT NULL DEFAULT '{}',
            version INTEGER NOT NULL DEFAULT 1,
            is_ai_generated BOOLEAN NOT NULL DEFAULT false,
            ai_justification TEXT,
            content TEXT NOT NULL,
            note_type note_type NOT NULL,
            note_metadata JSON NOT NULL DEFAULT '{}',
            CONSTRAINT ck_note_type CHECK (note_type IN ('fleeting', 'literature', 'permanent', 'insight', 'agent_generated')),
            CONSTRAINT ck_ai_justification_required CHECK (NOT (is_ai_generated AND ai_justification IS NULL))
        )
    """)

    op.execute("""
        CREATE TABLE embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            note_id UUID NOT NULL,
            vector vector(1536),
            model_version VARCHAR(100) NOT NULL,
            FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
        )
    """)

    op.execute("""
        CREATE TABLE links (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            created_by VARCHAR(255) NOT NULL,
            provenance JSON NOT NULL DEFAULT '{}',
            source_note_id UUID NOT NULL,
            target_note_id UUID NOT NULL,
            relation_type relation_type NOT NULL,
            FOREIGN KEY (source_note_id) REFERENCES notes(id) ON DELETE CASCADE,
            FOREIGN KEY (target_note_id) REFERENCES notes(id) ON DELETE CASCADE,
            CONSTRAINT ck_relation_type CHECK (relation_type IN ('cites', 'supports', 'derived_from', 'related', 'contradicts')),
            CONSTRAINT ck_no_self_reference CHECK (source_note_id != target_note_id)
        )
    """)

    op.execute("""
        CREATE TABLE agent_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            agent_name VARCHAR(255) NOT NULL,
            agent_version VARCHAR(100) NOT NULL,
            input_parameters JSON NOT NULL DEFAULT '{}',
            output_note_ids UUID[] NOT NULL DEFAULT '{}',
            status agent_run_status NOT NULL,
            started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            completed_at TIMESTAMP WITH TIME ZONE,
            error_details TEXT,
            human_reviewer VARCHAR(255),
            reviewed_at TIMESTAMP WITH TIME ZONE,
            review_status review_status,
            CONSTRAINT ck_agent_run_status CHECK (status IN ('success', 'failed', 'pending_review')),
            CONSTRAINT ck_review_status CHECK (review_status IN ('approved', 'rejected', 'needs_revision') OR review_status IS NULL)
        )
    """)

    op.execute("""
        CREATE TABLE version_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            created_by VARCHAR(255) NOT NULL,
            provenance JSON NOT NULL DEFAULT '{}',
            note_id UUID NOT NULL,
            version INTEGER NOT NULL,
            content TEXT NOT NULL,
            version_metadata JSON NOT NULL DEFAULT '{}',
            changes JSON NOT NULL DEFAULT '{}',
            change_reason TEXT,
            FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
        )
    """)

    # Create indexes using raw SQL
    op.execute("CREATE INDEX idx_notes_type ON notes (note_type)")
    op.execute("CREATE INDEX idx_notes_created_at ON notes (created_at)")
    op.execute("CREATE INDEX idx_notes_ai_generated ON notes (is_ai_generated)")
    op.execute("CREATE INDEX idx_embeddings_note_id ON embeddings (note_id)")
    op.execute("CREATE INDEX idx_links_source ON links (source_note_id)")
    op.execute("CREATE INDEX idx_links_target ON links (target_note_id)")
    op.execute("CREATE INDEX idx_agent_runs_status ON agent_runs (status)")
    op.execute("CREATE INDEX idx_agent_runs_agent ON agent_runs (agent_name, agent_version)")
    op.execute("CREATE INDEX idx_version_history_note_version ON version_history (note_id, version)")


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_version_history_note_version')
    op.drop_index('idx_agent_runs_agent')
    op.drop_index('idx_agent_runs_status')
    op.drop_index('idx_links_target')
    op.drop_index('idx_links_source')
    op.drop_index('idx_embeddings_note_id')
    op.drop_index('idx_notes_ai_generated')
    op.drop_index('idx_notes_created_at')
    op.drop_index('idx_notes_type')

    # Drop tables using raw SQL
    op.execute("DROP TABLE IF EXISTS version_history")
    op.execute("DROP TABLE IF EXISTS agent_runs")
    op.execute("DROP TABLE IF EXISTS links")
    op.execute("DROP TABLE IF EXISTS embeddings")
    op.execute("DROP TABLE IF EXISTS notes")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS review_status")
    op.execute("DROP TYPE IF EXISTS agent_run_status")
    op.execute("DROP TYPE IF EXISTS relation_type")
    op.execute("DROP TYPE IF EXISTS note_type")

    # Drop extensions
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
