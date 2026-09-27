"""add analytics foundation tables

Revision ID: 0009_intelligence_foundation
Revises: 0008_financial_core
"""

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_intelligence_foundation"
down_revision = "0008_financial_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domain_events.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metric_key", sa.String(80), nullable=False),
        sa.Column("scope_key", sa.String(160), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_analytics_events_tenant", "analytics_events", ["tenant_id"])
    op.create_index("ix_analytics_events_metric", "analytics_events", ["metric_key"])
    op.create_index("ix_analytics_events_scope", "analytics_events", ["scope_key"])

    op.create_table(
        "market_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("metric_key", sa.String(80), nullable=False),
        sa.Column("scope_key", sa.String(160), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("distinct_tenants", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "metric_key",
            "scope_key",
            "period_start",
            "period_end",
            name="uq_market_metric_period",
        ),
    )
    op.create_index("ix_market_metrics_metric", "market_metrics", ["metric_key"])
    op.create_index("ix_market_metrics_scope", "market_metrics", ["scope_key"])


def downgrade() -> None:
    op.drop_table("market_metrics")
    op.drop_table("analytics_events")
