"""add financial core tables

Revision ID: 0008_financial_core
Revises: 0007_shipments_deliveries
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008_financial_core"
down_revision = "0007_shipments_deliveries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commission_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("rate_percent", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.Column("fixed_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True),  # noqa: E501
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),  # noqa: E501
    )
    op.create_index("ix_commission_rules_tenant", "commission_rules", ["tenant_id"])
    op.create_index("ix_commission_rules_supplier", "commission_rules", ["supplier_id"])

    op.create_table(
        "order_financials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("gross_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("commission_rate", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.Column("commission_fixed_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("commission_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("supplier_net_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("status", sa.String(30), nullable=False, server_default="confirmed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),  # noqa: E501
        sa.UniqueConstraint("tenant_id", "order_id", name="uq_order_financial_tenant_order"),
    )
    op.create_index("ix_order_financials_tenant", "order_financials", ["tenant_id"])
    op.create_index("ix_order_financials_order", "order_financials", ["order_id"])

    op.create_table(
        "commissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("financial_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("order_financials.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("rate_percent", sa.Numeric(7, 4), nullable=False),
        sa.Column("fixed_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("base_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="generated"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),  # noqa: E501
        sa.UniqueConstraint("tenant_id", "order_id", name="uq_commission_tenant_order"),
    )
    op.create_index("ix_commissions_tenant", "commissions", ["tenant_id"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("flow", sa.String(40), nullable=False),
        sa.Column("method", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("provider_reference", sa.String(160), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),  # noqa: E501
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),  # noqa: E501
    )
    op.create_index("ix_payments_tenant", "payments", ["tenant_id"])
    op.create_index("ix_payments_order", "payments", ["order_id"])

    op.create_table(
        "settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("financial_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("order_financials.id", ondelete="CASCADE"), nullable=False),  # noqa: E501
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("provider_reference", sa.String(160), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),  # noqa: E501
        sa.UniqueConstraint("tenant_id", "order_id", name="uq_settlement_tenant_order"),
    )
    op.create_index("ix_settlements_tenant", "settlements", ["tenant_id"])
    op.create_index("ix_settlements_order", "settlements", ["order_id"])
    op.create_index("ix_settlements_supplier", "settlements", ["supplier_id"])


def downgrade() -> None:
    op.drop_table("settlements")
    op.drop_table("payments")
    op.drop_table("commissions")
    op.drop_table("order_financials")
    op.drop_table("commission_rules")
