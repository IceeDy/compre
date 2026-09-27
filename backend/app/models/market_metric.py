import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketMetric(Base):
    __tablename__ = "market_metrics"
    __table_args__ = (
        UniqueConstraint(
            "metric_key",
            "scope_key",
            "period_start",
            "period_end",
            name="uq_market_metric_period",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    scope_key: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    sample_size: Mapped[int] = mapped_column(nullable=False)
    distinct_tenants: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
