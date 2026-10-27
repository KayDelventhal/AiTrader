"""Persistent research domains, gathering and immutable source revisions.

Revision ID: 0003_research_gathering
Revises: 0002_workspace_costs
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_research_gathering"
down_revision = "0002_workspace_costs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('gathering_settings',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False))
    op.create_table('research_domains',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.String(length=40), nullable=False),
        sa.Column('updated_at', sa.String(length=40), nullable=False),
        sa.UniqueConstraint('name'))
    op.create_table('gathering_sources',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('catalog_key', sa.String(length=80), nullable=False),
        sa.Column('domain_ids', sa.JSON(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('interval_minutes', sa.Integer(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('next_due_at', sa.String(length=40), nullable=True),
        sa.Column('last_checked_at', sa.String(length=40), nullable=True),
        sa.Column('last_success_at', sa.String(length=40), nullable=True),
        sa.Column('last_error', sa.String(length=300), nullable=True),
        sa.Column('active_run_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.String(length=40), nullable=False),
        sa.Column('updated_at', sa.String(length=40), nullable=False),
        sa.UniqueConstraint('catalog_key'))
    op.create_table('gathering_runs',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('source_id', sa.String(length=64), sa.ForeignKey('gathering_sources.id'), nullable=False),
        sa.Column('trigger', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('requested_by', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.String(length=40), nullable=False),
        sa.Column('started_at', sa.String(length=40), nullable=True),
        sa.Column('completed_at', sa.String(length=40), nullable=True),
        sa.Column('snapshot', sa.JSON(), nullable=False),
        sa.Column('counts', sa.JSON(), nullable=False),
        sa.Column('result_metadata', sa.JSON(), nullable=False),
        sa.Column('error', sa.String(length=300), nullable=True))
    op.create_table('research_documents',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('identity_key', sa.String(length=64), nullable=False),
        sa.Column('source_id', sa.String(length=64), sa.ForeignKey('gathering_sources.id'), nullable=True),
        sa.Column('source_kind', sa.String(length=20), nullable=False),
        sa.Column('first_seen_at', sa.String(length=40), nullable=False),
        sa.Column('latest_revision', sa.Integer(), nullable=False),
        sa.UniqueConstraint('identity_key'))
    op.create_table('research_document_revisions',
        sa.Column('id', sa.String(length=64), primary_key=True, nullable=False),
        sa.Column('document_id', sa.String(length=64), sa.ForeignKey('research_documents.id'), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('recorded_at', sa.String(length=40), nullable=False),
        sa.Column('available_at', sa.String(length=40), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.UniqueConstraint('document_id', 'revision'))
    op.create_index('ix_research_document_revisions_document_id', 'research_document_revisions', ['document_id'])
    op.create_index('ix_research_document_revisions_available_at', 'research_document_revisions', ['available_at'])
    op.create_table('gathering_imports',
        sa.Column('idempotency_key', sa.String(length=120), primary_key=True, nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('actor_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.String(length=40), nullable=False),
        sa.Column('result', sa.JSON(), nullable=False))


def downgrade():
    op.drop_table('gathering_imports')
    op.drop_index('ix_research_document_revisions_document_id', table_name='research_document_revisions')
    op.drop_index('ix_research_document_revisions_available_at', table_name='research_document_revisions')
    op.drop_table('research_document_revisions')
    op.drop_table('research_documents')
    op.drop_table('gathering_runs')
    op.drop_table('gathering_sources')
    op.drop_table('research_domains')
    op.drop_table('gathering_settings')
