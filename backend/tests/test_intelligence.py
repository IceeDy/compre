from datetime import UTC, datetime
from decimal import Decimal

from app.models import Tenant
from app.services.intelligence import aggregate_market_metric, record_analytics_event


def _tenant(db, slug: str) -> Tenant:
    tenant = Tenant(name=slug.title(), slug=slug)
    db.add(tenant)
    db.flush()
    return tenant


def test_market_metric_requires_three_distinct_tenants(db):
    tenants = [_tenant(db, f"intel-{index}") for index in range(3)]
    occurred_at = datetime(2026, 9, 1, tzinfo=UTC)

    for index, tenant in enumerate(tenants, start=1):
        record_analytics_event(
            db,
            tenant_id=tenant.id,
            metric_key="price.average",
            scope_key="cafe-500g",
            value=Decimal(index),
            unit="BRL/unit",
            currency="brl",
            occurred_at=occurred_at,
        )

    metric = aggregate_market_metric(
        db,
        metric_key="price.average",
        scope_key="cafe-500g",
        period_start=occurred_at.date(),
        period_end=occurred_at.date(),
    )
    db.flush()

    assert metric is not None
    assert metric.value == Decimal("2.0000")
    assert metric.sample_size == 3
    assert metric.distinct_tenants == 3
    assert metric.currency == "BRL"


def test_market_metric_is_suppressed_below_threshold(db):
    tenants = [_tenant(db, f"intel-threshold-{index}") for index in range(2)]
    occurred_at = datetime(2026, 9, 2, tzinfo=UTC)

    for tenant in tenants:
        record_analytics_event(
            db,
            tenant_id=tenant.id,
            metric_key="lead_time.average",
            scope_key="cafe-500g",
            value=Decimal(3),
            unit="day",
            occurred_at=occurred_at,
        )

    metric = aggregate_market_metric(
        db,
        metric_key="lead_time.average",
        scope_key="cafe-500g",
        period_start=occurred_at.date(),
        period_end=occurred_at.date(),
    )

    assert metric is None
