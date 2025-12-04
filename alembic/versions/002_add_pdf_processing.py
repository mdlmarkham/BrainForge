"""Add PDF processing tables for ingestion pipeline.

Revision ID: 002_add_pdf_processing
Revises: 001_initial_migration
Create Date: 2025-11-29 00:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '002_add_pdf_processing'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types for ingestion pipeline with conditional checks
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'content_type') THEN
                CREATE TYPE content_type AS ENUM (
                    'web', 'video', 'text', 'pdf'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processing_state') THEN
                CREATE TYPE processing_state AS ENUM (
                    'validating', 'extracting_metadata', 'extracting_text',
                    'assessing_quality', 'summarizing', 'classifying',
                    'awaiting_review', 'integrated', 'failed'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'review_status') THEN
                CREATE TYPE review_status AS ENUM (
                    'pending', 'approved', 'rejected', 'needs_revision'
                );
            END IF;
        END $$;
    """)

    # Create ingestion_tasks table using raw SQL to avoid enum creation issues
    op.execute("""
        CREATE TABLE ingestion_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            created_by VARCHAR(255) NOT NULL,
            provenance JSON NOT NULL DEFAULT '{}',
            content_type content_type NOT NULL,
            source_url TEXT,
            file_name TEXT,
            file_size INTEGER,
            tags TEXT[] NOT NULL DEFAULT '{}',
            priority VARCHAR(10) NOT NULL DEFAULT 'normal',
            processing_state processing_state NOT NULL DEFAULT 'validating',
            processing_attempts INTEGER NOT NULL DEFAULT 0,
            last_processing_error TEXT,
            estimated_completion TIMESTAMP WITH TIME ZONE,
            CONSTRAINT ck_ingestion_priority CHECK (priority IN ('low', 'normal', 'high')),
            CONSTRAINT ck_max_processing_attempts CHECK (processing_attempts <= 3),
            CONSTRAINT ck_max_file_size CHECK (file_size IS NULL OR file_size <= 104857600)
        )
    """)

    # Create content_sources table
    op.execute("""
        CREATE TABLE content_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            ingestion_task_id UUID NOT NULL,
            source_type VARCHAR(50) NOT NULL,
            source_url TEXT,
            source_metadata JSON NOT NULL DEFAULT '{}',
            retrieval_method VARCHAR(100) NOT NULL,
            retrieval_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            content_hash VARCHAR(64) NOT NULL,
            FOREIGN KEY (ingestion_task_id) REFERENCES ingestion_tasks(id) ON DELETE CASCADE
        )
    """)

    # Create processing_results table
    op.execute("""
        CREATE TABLE processing_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            ingestion_task_id UUID NOT NULL,
            summary TEXT NOT NULL,
            classifications TEXT[] NOT NULL DEFAULT '{}',
            connection_suggestions JSON NOT NULL DEFAULT '[]',
            confidence_scores JSON NOT NULL DEFAULT '{}',
            processing_metadata JSON NOT NULL DEFAULT '{}',
            FOREIGN KEY (ingestion_task_id) REFERENCES ingestion_tasks(id) ON DELETE CASCADE
        )
    """)

    # Create pdf_metadata table
    op.execute("""
        CREATE TABLE pdf_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            ingestion_task_id UUID NOT NULL,
            page_count INTEGER NOT NULL,
            author TEXT,
            title TEXT,
            subject TEXT,
            creation_date TIMESTAMP WITH TIME ZONE,
            modification_date TIMESTAMP WITH TIME ZONE,
            pdf_version VARCHAR(10) NOT NULL,
            encryption_status VARCHAR(20) NOT NULL,
            extraction_method VARCHAR(50) NOT NULL,
            extraction_quality_score FLOAT NOT NULL,
            FOREIGN KEY (ingestion_task_id) REFERENCES ingestion_tasks(id) ON DELETE CASCADE,
            CONSTRAINT ck_encryption_status CHECK (encryption_status IN ('none', 'password', 'certificate')),
            CONSTRAINT ck_extraction_method CHECK (extraction_method IN ('dockling_basic', 'dockling_advanced', 'fallback')),
            CONSTRAINT ck_quality_score_range CHECK (extraction_quality_score >= 0.0 AND extraction_quality_score <= 1.0)
        )
    """)

    # Create pdf_processing_results table
    op.execute("""
        CREATE TABLE pdf_processing_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            ingestion_task_id UUID NOT NULL,
            extracted_text TEXT NOT NULL,
            text_quality_metrics JSON NOT NULL DEFAULT '{}',
            section_breaks JSON NOT NULL DEFAULT '{}',
            processing_time_ms INTEGER NOT NULL,
            dockling_version VARCHAR(20) NOT NULL,
            FOREIGN KEY (ingestion_task_id) REFERENCES ingestion_tasks(id) ON DELETE CASCADE,
            CONSTRAINT ck_processing_time_positive CHECK (processing_time_ms >= 0)
        )
    """)

    # Create review_queue table - first ensure the enum exists and has the correct values
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'review_status') THEN
                CREATE TYPE review_status AS ENUM (
                    'pending', 'approved', 'rejected', 'needs_revision'
                );
            ELSE
                -- If the enum exists but doesn't have 'pending', we need to handle this
                IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'review_status') AND enumlabel = 'pending') THEN
                    -- Drop and recreate the enum if it doesn't have the expected values
                    DROP TYPE IF EXISTS review_status CASCADE;
                    CREATE TYPE review_status AS ENUM (
                        'pending', 'approved', 'rejected', 'needs_revision'
                    );
                END IF;
            END IF;
        END $$;
    """)

    op.execute("""
        CREATE TABLE review_queue (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            ingestion_task_id UUID NOT NULL,
            review_status review_status NOT NULL DEFAULT 'pending',
            reviewer_id VARCHAR(255),
            reviewed_at TIMESTAMP WITH TIME ZONE,
            review_notes TEXT,
            priority INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (ingestion_task_id) REFERENCES ingestion_tasks(id) ON DELETE CASCADE
        )
    """)

    # Create audit_trail table
    op.execute("""
        CREATE TABLE audit_trail (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            ingestion_task_id UUID NOT NULL,
            action_type VARCHAR(100) NOT NULL,
            action_details JSON NOT NULL DEFAULT '{}',
            performed_by VARCHAR(255) NOT NULL,
            outcome VARCHAR(50) NOT NULL,
            error_details TEXT,
            FOREIGN KEY (ingestion_task_id) REFERENCES ingestion_tasks(id) ON DELETE CASCADE
        )
    """)

    # Create indexes for performance
    op.create_index('idx_ingestion_tasks_state', 'ingestion_tasks', ['processing_state'])
    op.create_index('idx_ingestion_tasks_type', 'ingestion_tasks', ['content_type'])
    op.create_index('idx_ingestion_tasks_priority', 'ingestion_tasks', ['priority'])
    op.create_index('idx_content_sources_task', 'content_sources', ['ingestion_task_id'])
    op.create_index('idx_content_sources_hash', 'content_sources', ['content_hash'])
    op.create_index('idx_processing_results_task', 'processing_results', ['ingestion_task_id'])
    op.create_index('idx_pdf_metadata_task', 'pdf_metadata', ['ingestion_task_id'])
    op.create_index('idx_pdf_processing_results_task', 'pdf_processing_results', ['ingestion_task_id'])
    op.create_index('idx_review_queue_status', 'review_queue', ['review_status'])
    op.create_index('idx_review_queue_priority', 'review_queue', ['priority'])
    op.create_index('idx_audit_trail_task', 'audit_trail', ['ingestion_task_id'])
    op.create_index('idx_audit_trail_action', 'audit_trail', ['action_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_audit_trail_action')
    op.drop_index('idx_audit_trail_task')
    op.drop_index('idx_review_queue_priority')
    op.drop_index('idx_review_queue_status')
    op.drop_index('idx_pdf_processing_results_task')
    op.drop_index('idx_pdf_metadata_task')
    op.drop_index('idx_processing_results_task')
    op.drop_index('idx_content_sources_hash')
    op.drop_index('idx_content_sources_task')
    op.drop_index('idx_ingestion_tasks_priority')
    op.drop_index('idx_ingestion_tasks_type')
    op.drop_index('idx_ingestion_tasks_state')

    # Drop tables
    op.execute('DROP TABLE IF EXISTS audit_trail')
    op.execute('DROP TABLE IF EXISTS review_queue')
    op.execute('DROP TABLE IF EXISTS pdf_processing_results')
    op.execute('DROP TABLE IF EXISTS pdf_metadata')
    op.execute('DROP TABLE IF EXISTS processing_results')
    op.execute('DROP TABLE IF EXISTS content_sources')
    op.execute('DROP TABLE IF EXISTS ingestion_tasks')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS review_status")
    op.execute("DROP TYPE IF EXISTS processing_state")
    op.execute("DROP TYPE IF EXISTS content_type")
