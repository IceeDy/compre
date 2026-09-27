from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AnalyticsEvent, MarketMetric

MIN_DISTINCT_TENANTS = 3


class IntelligenceGovernanceError(ValueError):
    pass


def record_analytics_event(
    db: Session,
    *,
    tenant_id: UUID,
    metric_key: str,
    scope_key: str,
    value: Decimal,
    unit: str,
    currency: str | None = None,
    occurred_at: datetime | None = None,
    source_event_id: UUID | None = None,
) -> AnalyticsEvent:
    if not metric_key or len(metric_key) > 80:
        raise IntelligenceGovernanceError("Invalid metric key")
    if not scope_key or len(scope_key) > 160:
        raise IntelligenceGovernanceError("Invalid scope key")
    if currency is not None and len(currency) != 3:
        raise IntelligenceGovernanceError("Currency must use ISO 4217 format")

    event = AnalyticsEvent(
        tenant_id=tenant_id,
        source_event_id=source_event_id,
        metric_key=metric_key,
        scope_key=scope_key,
        value=value,
        unit=unit,
        currency=currency.upper() if currency else None,
        occurred_at=occurred_at,
    )
    db.add(event)
    return event


def aggregate_market_metric(
    db: Session,
    *,
    metric_key: str,
    scope_key: str,
    period_start: date,
    period_end: date,
    minimum_distinct_tenants: int = MIN_DISTINCT_TENANTS,
) -> MarketMetric | None:
    if period_end < period_start:
        raise IntelligenceGovernanceError("Period end must not precede period start")
    if minimum_distinct_tenants < 1:
        raise IntelligenceGovernanceError("Minimum tenant threshold must be positive")

    rows = db.scalars(
        select(AnalyticsEvent).where(
            AnalyticsEvent.metric_key == metric_key,
            AnalyticsEvent.scope_key == scope_key,
            func.date(AnalyticsEvent.occurred_at) >= period_start,
            func.date(AnalyticsEvent.occurred_at) <= period_end,
        )
    ).all()
    if not rows:
        return None

    distinct_tenants = len({row.tenant_id for row in rows})
    if distinct_tenants < minimum_distinct_tenants:
        return None

    average = sum((row.value for row in rows), Decimal("0")) / len(rows)
    first = rows[0]
    metric = db.scalar(
        select(MarketMetric).where(
            MarketMetric.metric_key == metric_key,
            MarketMetric.scope_key == scope_key,
            MarketMetric.period_start == period_start,
            MarketMetric.period_end == period_end,
        )
    )
    if metric is None:
        metric = MarketMetric(
            metric_key=metric_key,
            scope_key=scope_key,
            period_start=period_start,
            period_end=period_end,
            value=average,
            unit=first.unit,
            currency=first.currency,
            sample_size=len(rows),
            distinct_tenants=distinct_tenants,
        )
        db.add(metric)
    else:
        metric.value = average
        metric.sample_size = len(rows)
        metric.distinct_tenants = distinct_tenants
        metric.unit = first.unit
        metric.currency = first.currency

    return metric
