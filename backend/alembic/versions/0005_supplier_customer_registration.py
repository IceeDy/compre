"""add asynchronous supplier customer registration workflow

Revision ID: 0005_supplier_customer_registration
Revises: 0004_governance_events
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_supplier_customer_registration"
down_revision = "0004_governance_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_customer_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "supplier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="requested"),
        sa.Column("external_reference", sa.String(120), nullable=True),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "tenant_id",
            "supplier_id",
            "customer_id",
            name="uq_supplier_customer_registration_scope",
        ),
    )
    op.create_index(
        "ix_supplier_customer_registrations_tenant",
        "supplier_customer_registrations",
        ["tenant_id"],
    )
    op.create_index(
        "ix_supplier_customer_registrations_supplier",
        "supplier_customer_registrations",
        ["supplier_id"],
    )
    op.create_index(
        "ix_supplier_customer_registrations_customer",
        "supplier_customer_registrations",
        ["customer_id"],
    )


def downgrade() -> None:
    op.drop_table("supplier_customer_registrations")
