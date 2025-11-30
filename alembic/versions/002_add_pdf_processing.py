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
    # Create enum types for ingestion pipeline
    op.execute("""
        CREATE TYPE content_type AS ENUM (
            'web', 'video', 'text', 'pdf'
        )
    """)

    op.execute("""
        CREATE TYPE processing_state AS ENUM (
            'validating', 'extracting_metadata', 'extracting_text', 
            'assessing_quality', 'summarizing', 'classifying', 
            'awaiting_review', 'integrated', 'failed'
        )
    """)

    op.execute("""
        CREATE TYPE review_status AS ENUM (
            'pending', 'approved', 'rejected', 'needs_revision'
        )
    """)

    # Create ingestion_tasks table
    op.create_table('ingestion_tasks',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('provenance', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('content_type', sa.Enum('web', 'video', 'text', 'pdf', name='content_type'), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('file_name', sa.Text(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('tags', sa.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('priority', sa.String(length=10), server_default='normal', nullable=False),
        sa.Column('processing_state', sa.Enum(
            'validating', 'extracting_metadata', 'extracting_text',
            'assessing_quality', 'summarizing', 'classifying',
            'awaiting_review', 'integrated', 'failed', name='processing_state'
        ), server_default='validating', nullable=False),
        sa.Column('processing_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_processing_error', sa.Text(), nullable=True),
        sa.Column('estimated_completion', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("priority IN ('low', 'normal', 'high')", name='ck_ingestion_priority'),
        sa.CheckConstraint("processing_attempts <= 3", name='ck_max_processing_attempts'),
        sa.CheckConstraint("file_size IS NULL OR file_size <= 104857600", name='ck_max_file_size')  # 100MB
    )

    # Create content_sources table
    op.create_table('content_sources',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ingestion_task_id', sa.UUID(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('retrieval_method', sa.String(length=100), nullable=False),
        sa.Column('retrieval_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['ingestion_task_id'], ['ingestion_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create processing_results table
    op.create_table('processing_results',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ingestion_task_id', sa.UUID(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('classifications', sa.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('connection_suggestions', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('confidence_scores', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('processing_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['ingestion_task_id'], ['ingestion_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create pdf_metadata table
    op.create_table('pdf_metadata',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ingestion_task_id', sa.UUID(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False),
        sa.Column('author', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('creation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('modification_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pdf_version', sa.String(length=10), nullable=False),
        sa.Column('encryption_status', sa.String(length=20), nullable=False),
        sa.Column('extraction_method', sa.String(length=50), nullable=False),
        sa.Column('extraction_quality_score', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['ingestion_task_id'], ['ingestion_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("encryption_status IN ('none', 'password', 'certificate')", name='ck_encryption_status'),
        sa.CheckConstraint("extraction_method IN ('dockling_basic', 'dockling_advanced', 'fallback')", name='ck_extraction_method'),
        sa.CheckConstraint("extraction_quality_score >= 0.0 AND extraction_quality_score <= 1.0", name='ck_quality_score_range')
    )

    # Create pdf_processing_results table
    op.create_table('pdf_processing_results',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ingestion_task_id', sa.UUID(), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('text_quality_metrics', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('section_breaks', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False),
        sa.Column('dockling_version', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['ingestion_task_id'], ['ingestion_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("processing_time_ms >= 0", name='ck_processing_time_positive')
    )

    # Create review_queue table
    op.create_table('review_queue',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ingestion_task_id', sa.UUID(), nullable=False),
        sa.Column('review_status', sa.Enum('pending', 'approved', 'rejected', 'needs_revision', name='review_status'), server_default='pending', nullable=False),
        sa.Column('reviewer_id', sa.String(length=255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['ingestion_task_id'], ['ingestion_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create audit_trail table
    op.create_table('audit_trail',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ingestion_task_id', sa.UUID(), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('action_details', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('performed_by', sa.String(length=255), nullable=False),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['ingestion_task_id'], ['ingestion_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

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
    op.drop_table('audit_trail')
    op.drop_table('review_queue')
    op.drop_table('pdf_processing_results')
    op.drop_table('pdf_metadata')
    op.drop_table('processing_results')
    op.drop_table('content_sources')
    op.drop_table('ingestion_tasks')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS review_status")
    op.execute("DROP TYPE IF EXISTS processing_state")
    op.execute("DROP TYPE IF EXISTS content_type")
