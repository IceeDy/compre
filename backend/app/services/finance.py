from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Commission, CommissionRule, Order, OrderFinancial, Settlement


def initialize_order_financial(
    db: Session,
    tenant_id: UUID,
    order: Order,
    rule: CommissionRule,
) -> OrderFinancial:
    existing = db.scalar(
        select(OrderFinancial).where(
            OrderFinancial.tenant_id == tenant_id,
            OrderFinancial.order_id == order.id,
        )
    )
    if existing:
        raise HTTPException(409, "Order financial snapshot already exists")

    rate = Decimal(rule.rate_percent)
    fixed = Decimal(rule.fixed_amount)
    commission = (Decimal(order.total) * rate / Decimal("100")) + fixed
    if commission > Decimal(order.total):
        raise HTTPException(422, "Commission cannot exceed order total")

    financial = OrderFinancial(
        tenant_id=tenant_id,
        order_id=order.id,
        gross_amount=order.total,
        commission_rate=rate,
        commission_fixed_amount=fixed,
        commission_amount=commission,
        supplier_net_amount=Decimal(order.total) - commission,
        currency="BRL",
        status="confirmed",
    )
    db.add(financial)
    db.flush()

    db.add(
        Commission(
            tenant_id=tenant_id,
            order_id=order.id,
            financial_id=financial.id,
            rate_percent=rate,
            fixed_amount=fixed,
            base_amount=order.total,
            amount=commission,
            status="generated",
        )
    )
    db.add(
        Settlement(
            tenant_id=tenant_id,
            order_id=order.id,
            supplier_id=order.proposal.supplier_id,
            financial_id=financial.id,
            amount=financial.supplier_net_amount,
            currency=financial.currency,
            status="pending",
        )
    )
    return financial
