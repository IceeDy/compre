"""add supplier fulfillment order workflow

Revision ID: 0006_supplier_orders
Revises: 0005_supplier_customer_registration
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_supplier_orders"
down_revision = "0005_supplier_customer_registration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="sent"),
        sa.Column("external_reference", sa.String(120), nullable=True),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "order_id", name="uq_supplier_order_tenant_order"),
    )
    op.create_index("ix_supplier_orders_tenant", "supplier_orders", ["tenant_id"])
    op.create_index("ix_supplier_orders_order", "supplier_orders", ["order_id"])
    op.create_index("ix_supplier_orders_supplier", "supplier_orders", ["supplier_id"])


def downgrade() -> None:
    op.drop_table("supplier_orders")
