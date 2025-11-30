"""Create MCP library tables

Revision ID: 004_mcp_library
Revises: 83aef568935a_add_user_authentication_tables
Create Date: 2025-11-29 18:47:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '004_mcp_library'
down_revision = '83aef568935a_add_user_authentication_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create mcp_tools table
    op.create_table('mcp_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('input_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('output_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('requires_auth', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('constitutional_gates', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create mcp_sessions table
    op.create_table('mcp_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_info', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('authentication_method', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_activity_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('constitutional_context', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create mcp_tool_executions table
    op.create_table('mcp_tool_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('input_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('output_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('constitutional_compliance', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tool_id'], ['mcp_tools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['mcp_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create mcp_workflows table
    op.create_table('mcp_workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('tool_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('constitutional_gates', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index('ix_mcp_tools_name', 'mcp_tools', ['name'])
    op.create_index('ix_mcp_tools_tags', 'mcp_tools', ['tags'], postgresql_using='gin')
    op.create_index('ix_mcp_sessions_user_id', 'mcp_sessions', ['user_id'])
    op.create_index('ix_mcp_sessions_agent_id', 'mcp_sessions', ['agent_id'])
    op.create_index('ix_mcp_sessions_is_active', 'mcp_sessions', ['is_active'])
    op.create_index('ix_mcp_tool_executions_tool_id', 'mcp_tool_executions', ['tool_id'])
    op.create_index('ix_mcp_tool_executions_session_id', 'mcp_tool_executions', ['session_id'])
    op.create_index('ix_mcp_tool_executions_status', 'mcp_tool_executions', ['status'])
    op.create_index('ix_mcp_tool_executions_created_at', 'mcp_tool_executions', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_mcp_tool_executions_created_at', table_name='mcp_tool_executions')
    op.drop_index('ix_mcp_tool_executions_status', table_name='mcp_tool_executions')
    op.drop_index('ix_mcp_tool_executions_session_id', table_name='mcp_tool_executions')
    op.drop_index('ix_mcp_tool_executions_tool_id', table_name='mcp_tool_executions')
    op.drop_index('ix_mcp_sessions_is_active', table_name='mcp_sessions')
    op.drop_index('ix_mcp_sessions_agent_id', table_name='mcp_sessions')
    op.drop_index('ix_mcp_sessions_user_id', table_name='mcp_sessions')
    op.drop_index('ix_mcp_tools_tags', table_name='mcp_tools')
    op.drop_index('ix_mcp_tools_name', table_name='mcp_tools')
    op.drop_table('mcp_workflows')
    op.drop_table('mcp_tool_executions')
    op.drop_table('mcp_sessions')
    op.drop_table('mcp_tools')
