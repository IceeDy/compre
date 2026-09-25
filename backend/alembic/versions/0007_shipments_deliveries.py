"""add shipment and delivery tracking

Revision ID: 0007_shipments_deliveries
Revises: 0006_supplier_orders
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_shipments_deliveries"
down_revision = "0006_supplier_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shipments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier_orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("carrier", sa.String(120), nullable=True),
        sa.Column("tracking_number", sa.String(120), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("estimated_delivery_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_shipments_tenant", "shipments", ["tenant_id"])

    op.create_table(
        "deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shipment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recipient_name", sa.String(160), nullable=True),
        sa.Column("proof_reference", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_deliveries_tenant", "deliveries", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("deliveries")
    op.drop_table("shipments")
