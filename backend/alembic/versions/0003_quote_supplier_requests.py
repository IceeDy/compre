"""track suppliers requested for quotes

Revision ID: 0003_quote_supplier_requests
Revises: 0002_commercial
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_quote_supplier_requests"
down_revision = "0002_commercial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quote_supplier_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "quote_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quotes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="requested"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("responded_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("quote_id", "supplier_id", name="uq_quote_supplier_request"),
    )
    op.create_index("ix_quote_supplier_requests_tenant_id", "quote_supplier_requests", ["tenant_id"])
    op.create_index("ix_quote_supplier_requests_quote_id", "quote_supplier_requests", ["quote_id"])
    op.create_index("ix_quote_supplier_requests_supplier_id", "quote_supplier_requests", ["supplier_id"])


def downgrade() -> None:
    op.drop_table("quote_supplier_requests")
