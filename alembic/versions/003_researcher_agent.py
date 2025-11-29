"""Add researcher agent tables for automated content discovery and evaluation.

Revision ID: 003_researcher_agent
Revises: 002_add_pdf_processing
Create Date: 2025-11-29 02:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_researcher_agent'
down_revision = '002_add_pdf_processing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types for researcher agent
    op.execute("""
        CREATE TYPE research_run_status AS ENUM (
            'pending', 'running', 'completed', 'failed', 'cancelled'
        )
    """)
    
    op.execute("""
        CREATE TYPE content_source_type AS ENUM (
            'web_article', 'academic_paper', 'news_report', 'blog_post', 'technical_document'
        )
    """)
    
    op.execute("""
        CREATE TYPE quality_score_type AS ENUM (
            'credibility', 'relevance', 'freshness', 'completeness', 'overall'
        )
    """)
    
    op.execute("""
        CREATE TYPE integration_proposal_status AS ENUM (
            'pending_review', 'approved', 'rejected', 'integrated'
        )
    """)
    
    op.execute("""
        CREATE TYPE audit_action_type AS ENUM (
            'research_started', 'content_discovered', 'quality_assessed', 
            'review_assigned', 'review_completed', 'integration_proposed'
        )
    """)
    
    # Create research_runs table
    op.create_table('research_runs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('provenance', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('research_topic', sa.Text(), nullable=False),
        sa.Column('research_parameters', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='research_run_status'), server_default='pending', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_sources_discovered', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_sources_assessed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_sources_approved', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('performance_metrics', sa.JSON(), server_default='{}', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'cancelled')", name='ck_research_run_status'),
        sa.CheckConstraint("total_sources_discovered >= 0", name='ck_sources_discovered_positive'),
        sa.CheckConstraint("total_sources_assessed >= 0", name='ck_sources_assessed_positive'),
        sa.CheckConstraint("total_sources_approved >= 0", name='ck_sources_approved_positive')
    )
    
    # Create content_sources_research table (extends existing content_sources)
    op.create_table('content_sources_research',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('research_run_id', sa.UUID(), nullable=False),
        sa.Column('source_type', sa.Enum('web_article', 'academic_paper', 'news_report', 'blog_post', 'technical_document', name='content_source_type'), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('source_title', sa.Text(), nullable=False),
        sa.Column('source_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('retrieval_method', sa.String(length=100), nullable=False),
        sa.Column('retrieval_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('duplicate_of', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['research_run_id'], ['research_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['duplicate_of'], ['content_sources_research.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("source_type IN ('web_article', 'academic_paper', 'news_report', 'blog_post', 'technical_document')", name='ck_content_source_type')
    )
    
    # Create quality_assessments table
    op.create_table('quality_assessments',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('content_source_id', sa.UUID(), nullable=False),
        sa.Column('score_type', sa.Enum('credibility', 'relevance', 'freshness', 'completeness', 'overall', name='quality_score_type'), nullable=False),
        sa.Column('score_value', sa.Float(), nullable=False),
        sa.Column('score_rationale', sa.Text(), nullable=False),
        sa.Column('confidence_level', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('assessment_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['content_source_id'], ['content_sources_research.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("score_type IN ('credibility', 'relevance', 'freshness', 'completeness', 'overall')", name='ck_quality_score_type'),
        sa.CheckConstraint("score_value >= 0.0 AND score_value <= 1.0", name='ck_score_value_range'),
        sa.CheckConstraint("confidence_level >= 0.0 AND confidence_level <= 1.0", name='ck_confidence_level_range')
    )
    
    # Create review_queue_research table (extends existing review_queue)
    op.create_table('review_queue_research',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('content_source_id', sa.UUID(), nullable=False),
        sa.Column('review_status', sa.Enum('pending', 'approved', 'rejected', 'needs_revision', name='review_status'), server_default='pending', nullable=False),
        sa.Column('reviewer_id', sa.String(length=255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
        sa.Column('auto_assessment_summary', sa.Text(), nullable=False),
        sa.Column('integration_suggestions', sa.JSON(), server_default='[]', nullable=False),
        sa.ForeignKeyConstraint(['content_source_id'], ['content_sources_research.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create integration_proposals table
    op.create_table('integration_proposals',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('content_source_id', sa.UUID(), nullable=False),
        sa.Column('proposal_status', sa.Enum('pending_review', 'approved', 'rejected', 'integrated', name='integration_proposal_status'), server_default='pending_review', nullable=False),
        sa.Column('proposed_note_content', sa.Text(), nullable=False),
        sa.Column('proposed_tags', sa.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('connection_suggestions', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('integration_confidence', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('integration_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('integrated_note_id', sa.UUID(), nullable=True),
        sa.Column('integration_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['content_source_id'], ['content_sources_research.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['integrated_note_id'], ['notes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("proposal_status IN ('pending_review', 'approved', 'rejected', 'integrated')", name='ck_integration_proposal_status'),
        sa.CheckConstraint("integration_confidence >= 0.0 AND integration_confidence <= 1.0", name='ck_integration_confidence_range')
    )
    
    # Create research_audit_trail table
    op.create_table('research_audit_trail',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('research_run_id', sa.UUID(), nullable=False),
        sa.Column('action_type', sa.Enum('research_started', 'content_discovered', 'quality_assessed', 'review_assigned', 'review_completed', 'integration_proposed', name='audit_action_type'), nullable=False),
        sa.Column('action_details', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('performed_by', sa.String(length=255), nullable=False),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('performance_metrics', sa.JSON(), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['research_run_id'], ['research_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("action_type IN ('research_started', 'content_discovered', 'quality_assessed', 'review_assigned', 'review_completed', 'integration_proposed')", name='ck_audit_action_type')
    )
    
    # Create indexes for performance
    op.create_index('idx_research_runs_status', 'research_runs', ['status'])
    op.create_index('idx_research_runs_topic', 'research_runs', ['research_topic'])
    op.create_index('idx_research_runs_created', 'research_runs', ['created_at'])
    op.create_index('idx_content_sources_research_run', 'content_sources_research', ['research_run_id'])
    op.create_index('idx_content_sources_type', 'content_sources_research', ['source_type'])
    op.create_index('idx_content_sources_hash', 'content_sources_research', ['content_hash'])
    op.create_index('idx_quality_assessments_source', 'quality_assessments', ['content_source_id'])
    op.create_index('idx_quality_assessments_type', 'quality_assessments', ['score_type'])
    op.create_index('idx_review_queue_research_status', 'review_queue_research', ['review_status'])
    op.create_index('idx_review_queue_research_priority', 'review_queue_research', ['priority'])
    op.create_index('idx_integration_proposals_status', 'integration_proposals', ['proposal_status'])
    op.create_index('idx_integration_proposals_confidence', 'integration_proposals', ['integration_confidence'])
    op.create_index('idx_research_audit_trail_run', 'research_audit_trail', ['research_run_id'])
    op.create_index('idx_research_audit_trail_action', 'research_audit_trail', ['action_type'])


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
    
    # Drop tables
    op.drop_table('research_audit_trail')
    op.drop_table('integration_proposals')
    op.drop_table('review_queue_research')
    op.drop_table('quality_assessments')
    op.drop_table('content_sources_research')
    op.drop_table('research_runs')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS audit_action_type")
    op.execute("DROP TYPE IF EXISTS integration_proposal_status")
    op.execute("DROP TYPE IF EXISTS quality_score_type")
    op.execute("DROP TYPE IF EXISTS content_source_type")
    op.execute("DROP TYPE IF EXISTS research_run_status")