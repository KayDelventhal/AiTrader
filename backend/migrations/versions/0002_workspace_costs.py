"""Workspace configuration and operating cost ledger.

Revision ID: 0002_workspace_costs
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_workspace_costs"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("workspace_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("markets", sa.JSON(), nullable=False),
        sa.Column("horizon", sa.String(30), nullable=False),
        sa.Column("monthly_limit_micros", sa.Integer(), nullable=False),
        sa.Column("warning_pct", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False))
    op.create_table("workspace_settings_revisions",
        sa.Column("revision", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False))
    op.create_table("budget_months",
        sa.Column("month", sa.String(7), primary_key=True),
        sa.Column("limit_micros", sa.Integer(), nullable=False),
        sa.Column("settings_revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False))
    op.create_table("cost_entries",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("idempotency_key", sa.String(160), nullable=False, unique=True),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("month", sa.String(7), sa.ForeignKey("budget_months.month"), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("amount_micros", sa.Integer(), nullable=True),
        sa.Column("reserved_micros", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("original_amount", sa.String(50), nullable=True),
        sa.Column("fx_rate", sa.String(50), nullable=True),
        sa.Column("fx_as_of", sa.String(40), nullable=True),
        sa.Column("pricing_version", sa.String(120), nullable=False),
        sa.Column("run_id", sa.String(64), nullable=True),
        sa.Column("strategy_id", sa.String(64), nullable=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False))
    op.create_index("ix_cost_entries_month", "cost_entries", ["month"])
    op.create_table("cost_revisions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entry_id", sa.String(64), sa.ForeignKey("cost_entries.id"), nullable=False),
        sa.Column("event_key", sa.String(120), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("note", sa.String(500), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint("entry_id", "event_key"), sa.UniqueConstraint("entry_id", "revision"))
    op.create_table("recurring_costs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("idempotency_key", sa.String(120), nullable=False, unique=True),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("monthly_amount_micros", sa.Integer(), nullable=False),
        sa.Column("start_month", sa.String(7), nullable=False),
        sa.Column("end_month", sa.String(7), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("stop_event_key", sa.String(120), nullable=True),
        sa.Column("stop_request_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.String(40), nullable=False))


def downgrade():
    op.drop_table("recurring_costs")
    op.drop_table("cost_revisions")
    op.drop_index("ix_cost_entries_month", table_name="cost_entries")
    op.drop_table("cost_entries")
    op.drop_table("budget_months")
    op.drop_table("workspace_settings_revisions")
    op.drop_table("workspace_settings")
