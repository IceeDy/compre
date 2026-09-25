import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrderFinancial(Base):
    __tablename__ = "order_financials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "order_id", name="uq_order_financial_tenant_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    commission_fixed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    supplier_net_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="confirmed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    order = relationship("Order")
