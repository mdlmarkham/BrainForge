"""Initial migration for BrainForge database.

Revision ID: 001_initial_migration
Revises: 
Create Date: 2025-11-28 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create enum types
    op.execute("""
        CREATE TYPE note_type AS ENUM (
            'fleeting', 'literature', 'permanent', 'insight', 'agent_generated'
        )
    """)
    
    op.execute("""
        CREATE TYPE relation_type AS ENUM (
            'cites', 'supports', 'derived_from', 'related', 'contradicts'
        )
    """)
    
    op.execute("""
        CREATE TYPE agent_run_status AS ENUM (
            'success', 'failed', 'pending_review'
        )
    """)
    
    op.execute("""
        CREATE TYPE review_status AS ENUM (
            'approved', 'rejected', 'needs_revision'
        )
    """)
    
    # Create tables
    op.create_table('notes',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('provenance', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_ai_generated', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ai_justification', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('note_type', sa.Enum('fleeting', 'literature', 'permanent', 'insight', 'agent_generated', name='note_type'), nullable=False),
        sa.Column('note_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("note_type IN ('fleeting', 'literature', 'permanent', 'insight', 'agent_generated')", name='ck_note_type'),
        sa.CheckConstraint("NOT (is_ai_generated AND ai_justification IS NULL)", name='ck_ai_justification_required')
    )
    
    op.create_table('embeddings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('note_id', sa.UUID(), nullable=False),
        sa.Column('vector', Vector(1536), nullable=True),
        sa.Column('model_version', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('links',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('provenance', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('source_note_id', sa.UUID(), nullable=False),
        sa.Column('target_note_id', sa.UUID(), nullable=False),
        sa.Column('relation_type', sa.Enum('cites', 'supports', 'derived_from', 'related', 'contradicts', name='relation_type'), nullable=False),
        sa.ForeignKeyConstraint(['source_note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("relation_type IN ('cites', 'supports', 'derived_from', 'related', 'contradicts')", name='ck_relation_type'),
        sa.CheckConstraint("source_note_id != target_note_id", name='ck_no_self_reference')
    )
    
    op.create_table('agent_runs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('agent_name', sa.String(length=255), nullable=False),
        sa.Column('agent_version', sa.String(length=100), nullable=False),
        sa.Column('input_parameters', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('output_note_ids', sa.ARRAY(sa.UUID()), server_default='{}', nullable=False),
        sa.Column('status', sa.Enum('success', 'failed', 'pending_review', name='agent_run_status'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('human_reviewer', sa.String(length=255), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_status', sa.Enum('approved', 'rejected', 'needs_revision', name='review_status'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('success', 'failed', 'pending_review')", name='ck_agent_run_status'),
        sa.CheckConstraint("review_status IN ('approved', 'rejected', 'needs_revision') OR review_status IS NULL", name='ck_review_status')
    )
    
    op.create_table('version_history',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('provenance', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('note_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('changes', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_notes_type', 'notes', ['note_type'])
    op.create_index('idx_notes_created_at', 'notes', ['created_at'])
    op.create_index('idx_notes_ai_generated', 'notes', ['is_ai_generated'])
    op.create_index('idx_embeddings_note_id', 'embeddings', ['note_id'])
    op.create_index('idx_links_source', 'links', ['source_note_id'])
    op.create_index('idx_links_target', 'links', ['target_note_id'])
    op.create_index('idx_agent_runs_status', 'agent_runs', ['status'])
    op.create_index('idx_agent_runs_agent', 'agent_runs', ['agent_name', 'agent_version'])
    op.create_index('idx_version_history_note_version', 'version_history', ['note_id', 'version'])


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
    
    # Drop tables
    op.drop_table('version_history')
    op.drop_table('agent_runs')
    op.drop_table('links')
    op.drop_table('embeddings')
    op.drop_table('notes')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS review_status")
    op.execute("DROP TYPE IF EXISTS agent_run_status")
    op.execute("DROP TYPE IF EXISTS relation_type")
    op.execute("DROP TYPE IF EXISTS note_type")
    
    # Drop extensions
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")