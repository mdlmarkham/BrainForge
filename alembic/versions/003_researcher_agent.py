"""Add researcher agent tables for automated content discovery and evaluation.

Revision ID: 003_researcher_agent
Revises: 002_add_pdf_processing
Create Date: 2025-11-29 02:15:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '003_researcher_agent'
down_revision = '002_add_pdf_processing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types for researcher agent with conditional creation
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'research_run_status') THEN
                CREATE TYPE research_run_status AS ENUM (
                    'pending', 'running', 'completed', 'failed', 'cancelled'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'content_source_type') THEN
                CREATE TYPE content_source_type AS ENUM (
                    'web_article', 'academic_paper', 'news_report', 'blog_post', 'technical_document'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'quality_score_type') THEN
                CREATE TYPE quality_score_type AS ENUM (
                    'credibility', 'relevance', 'freshness', 'completeness', 'overall'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'integration_proposal_status') THEN
                CREATE TYPE integration_proposal_status AS ENUM (
                    'pending_review', 'approved', 'rejected', 'integrated'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audit_action_type') THEN
                CREATE TYPE audit_action_type AS ENUM (
                    'research_started', 'content_discovered', 'quality_assessed',
                    'review_assigned', 'review_completed', 'integration_proposed'
                );
            END IF;
        END $$;
    """)

    # Create research_runs table using raw SQL to avoid SQLAlchemy enum conflicts
    op.execute("""
        CREATE TABLE research_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            created_by VARCHAR(255) NOT NULL,
            provenance JSONB NOT NULL DEFAULT '{}',
            research_topic TEXT NOT NULL,
            research_parameters JSONB NOT NULL DEFAULT '{}',
            status research_run_status NOT NULL DEFAULT 'pending',
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            total_sources_discovered INTEGER NOT NULL DEFAULT 0,
            total_sources_assessed INTEGER NOT NULL DEFAULT 0,
            total_sources_approved INTEGER NOT NULL DEFAULT 0,
            error_details TEXT,
            performance_metrics JSONB NOT NULL DEFAULT '{}',
            CONSTRAINT ck_research_run_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
            CONSTRAINT ck_sources_discovered_positive CHECK (total_sources_discovered >= 0),
            CONSTRAINT ck_sources_assessed_positive CHECK (total_sources_assessed >= 0),
            CONSTRAINT ck_sources_approved_positive CHECK (total_sources_approved >= 0)
        )
    """)

    # Create content_sources_research table (extends existing content_sources) using raw SQL
    op.execute("""
        CREATE TABLE content_sources_research (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            research_run_id UUID NOT NULL,
            source_type content_source_type NOT NULL,
            source_url TEXT NOT NULL,
            source_title TEXT NOT NULL,
            source_metadata JSONB NOT NULL DEFAULT '{}',
            retrieval_method VARCHAR(100) NOT NULL,
            retrieval_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            content_hash VARCHAR(64) NOT NULL,
            raw_content TEXT,
            is_duplicate BOOLEAN NOT NULL DEFAULT false,
            duplicate_of UUID,
            FOREIGN KEY (research_run_id) REFERENCES research_runs(id) ON DELETE CASCADE,
            FOREIGN KEY (duplicate_of) REFERENCES content_sources_research(id) ON DELETE SET NULL,
            CONSTRAINT ck_content_source_type CHECK (source_type IN ('web_article', 'academic_paper', 'news_report', 'blog_post', 'technical_document'))
        )
    """)

    # Create quality_assessments table using raw SQL
    op.execute("""
        CREATE TABLE quality_assessments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            content_source_id UUID NOT NULL,
            score_type quality_score_type NOT NULL,
            score_value FLOAT NOT NULL,
            score_rationale TEXT NOT NULL,
            confidence_level FLOAT NOT NULL DEFAULT 1.0,
            assessment_metadata JSONB NOT NULL DEFAULT '{}',
            FOREIGN KEY (content_source_id) REFERENCES content_sources_research(id) ON DELETE CASCADE,
            CONSTRAINT ck_quality_score_type CHECK (score_type IN ('credibility', 'relevance', 'freshness', 'completeness', 'overall')),
            CONSTRAINT ck_score_value_range CHECK (score_value >= 0.0 AND score_value <= 1.0),
            CONSTRAINT ck_confidence_level_range CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0)
        )
    """)

    # Create review_queue_research table (extends existing review_queue) using raw SQL
    op.execute("""
        CREATE TABLE review_queue_research (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            content_source_id UUID NOT NULL,
            review_status review_status NOT NULL DEFAULT 'pending',
            reviewer_id VARCHAR(255),
            reviewed_at TIMESTAMP WITH TIME ZONE,
            review_notes TEXT,
            priority INTEGER NOT NULL DEFAULT 0,
            auto_assessment_summary TEXT NOT NULL,
            integration_suggestions JSONB NOT NULL DEFAULT '[]',
            FOREIGN KEY (content_source_id) REFERENCES content_sources_research(id) ON DELETE CASCADE
        )
    """)

    # Create integration_proposals table using raw SQL
    op.execute("""
        CREATE TABLE integration_proposals (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            content_source_id UUID NOT NULL,
            proposal_status integration_proposal_status NOT NULL DEFAULT 'pending_review',
            proposed_note_content TEXT NOT NULL,
            proposed_tags TEXT[] NOT NULL DEFAULT '{}',
            connection_suggestions JSONB NOT NULL DEFAULT '[]',
            integration_confidence FLOAT NOT NULL DEFAULT 0.0,
            integration_metadata JSONB NOT NULL DEFAULT '{}',
            integrated_note_id UUID,
            integration_timestamp TIMESTAMP WITH TIME ZONE,
            FOREIGN KEY (content_source_id) REFERENCES content_sources_research(id) ON DELETE CASCADE,
            FOREIGN KEY (integrated_note_id) REFERENCES notes(id) ON DELETE SET NULL,
            CONSTRAINT ck_integration_proposal_status CHECK (proposal_status IN ('pending_review', 'approved', 'rejected', 'integrated')),
            CONSTRAINT ck_integration_confidence_range CHECK (integration_confidence >= 0.0 AND integration_confidence <= 1.0)
        )
    """)

    # Create research_audit_trail table using raw SQL
    op.execute("""
        CREATE TABLE research_audit_trail (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            research_run_id UUID NOT NULL,
            action_type audit_action_type NOT NULL,
            action_details JSONB NOT NULL DEFAULT '{}',
            performed_by VARCHAR(255) NOT NULL,
            outcome VARCHAR(50) NOT NULL,
            error_details TEXT,
            performance_metrics JSONB NOT NULL DEFAULT '{}',
            FOREIGN KEY (research_run_id) REFERENCES research_runs(id) ON DELETE CASCADE,
            CONSTRAINT ck_audit_action_type CHECK (action_type IN ('research_started', 'content_discovered', 'quality_assessed', 'review_assigned', 'review_completed', 'integration_proposed'))
        )
    """)

    # Create indexes for performance with conditional creation
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_research_runs_status') THEN
                CREATE INDEX idx_research_runs_status ON research_runs (status);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_research_runs_topic') THEN
                CREATE INDEX idx_research_runs_topic ON research_runs (research_topic);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_research_runs_created') THEN
                CREATE INDEX idx_research_runs_created ON research_runs (created_at);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_content_sources_research_run') THEN
                CREATE INDEX idx_content_sources_research_run ON content_sources_research (research_run_id);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_content_sources_type') THEN
                CREATE INDEX idx_content_sources_type ON content_sources_research (source_type);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_content_sources_hash') THEN
                CREATE INDEX idx_content_sources_hash ON content_sources_research (content_hash);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_quality_assessments_source') THEN
                CREATE INDEX idx_quality_assessments_source ON quality_assessments (content_source_id);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_quality_assessments_type') THEN
                CREATE INDEX idx_quality_assessments_type ON quality_assessments (score_type);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_review_queue_research_status') THEN
                CREATE INDEX idx_review_queue_research_status ON review_queue_research (review_status);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_review_queue_research_priority') THEN
                CREATE INDEX idx_review_queue_research_priority ON review_queue_research (priority);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_integration_proposals_status') THEN
                CREATE INDEX idx_integration_proposals_status ON integration_proposals (proposal_status);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_integration_proposals_confidence') THEN
                CREATE INDEX idx_integration_proposals_confidence ON integration_proposals (integration_confidence);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_research_audit_trail_run') THEN
                CREATE INDEX idx_research_audit_trail_run ON research_audit_trail (research_run_id);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_research_audit_trail_action') THEN
                CREATE INDEX idx_research_audit_trail_action ON research_audit_trail (action_type);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_research_audit_trail_action')
    op.drop_index('idx_research_audit_trail_run')
    op.drop_index('idx_integration_proposals_confidence')
    op.drop_index('idx_integration_proposals_status')
    op.drop_index('idx_review_queue_research_priority')
    op.drop_index('idx_review_queue_research_status')
    op.drop_index('idx_quality_assessments_type')
    op.drop_index('idx_quality_assessments_source')
    op.drop_index('idx_content_sources_hash')
    op.drop_index('idx_content_sources_type')
    op.drop_index('idx_content_sources_research_run')
    op.drop_index('idx_research_runs_created')
    op.drop_index('idx_research_runs_topic')
    op.drop_index('idx_research_runs_status')

    # Drop tables using raw SQL
    op.execute("DROP TABLE IF EXISTS research_audit_trail")
    op.execute("DROP TABLE IF EXISTS integration_proposals")
    op.execute("DROP TABLE IF EXISTS review_queue_research")
    op.execute("DROP TABLE IF EXISTS quality_assessments")
    op.execute("DROP TABLE IF EXISTS content_sources_research")
    op.execute("DROP TABLE IF EXISTS research_runs")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS audit_action_type")
    op.execute("DROP TYPE IF EXISTS integration_proposal_status")
    op.execute("DROP TYPE IF EXISTS quality_score_type")
    op.execute("DROP TYPE IF EXISTS content_source_type")
    op.execute("DROP TYPE IF EXISTS research_run_status")
