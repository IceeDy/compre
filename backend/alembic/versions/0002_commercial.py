"""create commercial workflow tables

Revision ID: 0002_commercial
Revises: 0001_identity
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_commercial"
down_revision = "0001_identity"
branch_labels = None
depends_on = None


def col(name, fk=None, **kw):
    args = [postgresql.UUID(as_uuid=True)]
    if fk:
        args.append(sa.ForeignKey(fk, ondelete=kw.pop("ondelete", None)))
    return sa.Column(name, *args, **kw)


def upgrade() -> None:
    op.create_table("customers",
        col("id", primary_key=True, nullable=False),
        col("tenant_id", "tenants.id", ondelete="CASCADE", nullable=False),
        sa.Column("name", sa.String(180), nullable=False), sa.Column("document", sa.String(30)),
        sa.Column("email", sa.String(320)), sa.Column("phone", sa.String(30)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])

    op.create_table("suppliers",
        col("id", primary_key=True, nullable=False),
        col("tenant_id", "tenants.id", ondelete="CASCADE", nullable=False),
        sa.Column("name", sa.String(180), nullable=False), sa.Column("document", sa.String(30)),
        sa.Column("email", sa.String(320)), sa.Column("phone", sa.String(30)),
        sa.Column("registration_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_suppliers_tenant_id", "suppliers", ["tenant_id"])

    op.create_table("products",
        col("id", primary_key=True, nullable=False),
        col("tenant_id", "tenants.id", ondelete="CASCADE", nullable=False),
        sa.Column("sku", sa.String(80), nullable=False), sa.Column("name", sa.String(220), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False, server_default="UN"), sa.Column("category", sa.String(100)),
        sa.Column("reference_price", sa.Numeric(14,2)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"])

    op.create_table("quotes",
        col("id", primary_key=True, nullable=False), col("tenant_id", "tenants.id", ondelete="CASCADE", nullable=False),
        col("customer_id", "customers.id", nullable=False), sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("notes", sa.String(1000)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_quotes_tenant_id", "quotes", ["tenant_id"])

    op.create_table("quote_items",
        col("id", primary_key=True, nullable=False), col("quote_id", "quotes.id", ondelete="CASCADE", nullable=False),
        col("product_id", "products.id", nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("target_price", sa.Numeric(14,2)))
    op.create_index("ix_quote_items_quote_id", "quote_items", ["quote_id"])

    op.create_table("proposals",
        col("id", primary_key=True, nullable=False), col("tenant_id", "tenants.id", ondelete="CASCADE", nullable=False),
        col("quote_id", "quotes.id", ondelete="CASCADE", nullable=False), col("supplier_id", "suppliers.id", nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="received"), sa.Column("total", sa.Numeric(14,2), nullable=False, server_default="0"),
        sa.Column("valid_until", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_proposals_tenant_id", "proposals", ["tenant_id"])
    op.create_index("ix_proposals_quote_id", "proposals", ["quote_id"])

    op.create_table("proposal_items",
        col("id", primary_key=True, nullable=False), col("proposal_id", "proposals.id", ondelete="CASCADE", nullable=False),
        col("quote_item_id", "quote_items.id", nullable=False), sa.Column("unit_price", sa.Numeric(14,2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("total", sa.Numeric(14,2), nullable=False))
    op.create_index("ix_proposal_items_proposal_id", "proposal_items", ["proposal_id"])

    op.create_table("orders",
        col("id", primary_key=True, nullable=False), col("tenant_id", "tenants.id", ondelete="CASCADE", nullable=False),
        col("customer_id", "customers.id", nullable=False), col("proposal_id", "proposals.id", nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"), sa.Column("total", sa.Numeric(14,2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_orders_tenant_id", "orders", ["tenant_id"])

    op.create_table("order_items",
        col("id", primary_key=True, nullable=False), col("order_id", "orders.id", ondelete="CASCADE", nullable=False),
        col("product_id", "products.id", nullable=False), sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(14,2), nullable=False), sa.Column("total", sa.Numeric(14,2), nullable=False))
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade() -> None:
    for name in ["order_items", "orders", "proposal_items", "proposals", "quote_items", "quotes", "products", "suppliers", "customers"]:
        op.drop_table(name)
