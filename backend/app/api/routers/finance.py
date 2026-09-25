from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models import CommissionRule, Order, OrderFinancial, Payment, Settlement, Supplier
from app.schemas.finance import (
    CommissionRuleCreate,
    CommissionRuleResponse,
    FinancialInitializeRequest,
    OrderFinancialResponse,
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
    SettlementResponse,
)
from app.services.finance import initialize_order_financial
from app.services.governance import record_audit, record_event

router = APIRouter(prefix="/finance", tags=["finance"])


@router.post(
    "/commission-rules",
    response_model=CommissionRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_commission_rule(payload: CommissionRuleCreate, user: CurrentUser, db: DbSession):
    if payload.supplier_id:
        supplier = db.scalar(
            select(Supplier).where(
                Supplier.id == payload.supplier_id,
                Supplier.tenant_id == user.tenant_id,
                Supplier.is_active.is_(True),
            )
        )
        if not supplier:
            raise HTTPException(404, "Supplier not found")
    rule = CommissionRule(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/commission-rules", response_model=list[CommissionRuleResponse])
def list_commission_rules(user: CurrentUser, db: DbSession):
    return db.scalars(
        select(CommissionRule)
        .where(CommissionRule.tenant_id == user.tenant_id)
        .order_by(CommissionRule.created_at.desc())
    ).all()


@router.post(
    "/orders/{order_id}/initialize",
    response_model=OrderFinancialResponse,
    status_code=status.HTTP_201_CREATED,
)
def initialize_financial(
    order_id: str, payload: FinancialInitializeRequest, user: CurrentUser, db: DbSession
):
    order = db.scalar(
        select(Order)
        .options(selectinload(Order.proposal))
        .where(Order.id == order_id, Order.tenant_id == user.tenant_id)
    )
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status not in {"released", "pending"}:
        raise HTTPException(409, "Order is not eligible for financial initialization")

    if payload.commission_rule_id:
        rule = db.scalar(
            select(CommissionRule).where(
                CommissionRule.id == payload.commission_rule_id,
                CommissionRule.tenant_id == user.tenant_id,
                CommissionRule.is_active.is_(True),
            )
        )
        if not rule:
            raise HTTPException(404, "Commission rule not found")
    else:
        rule = db.scalar(
            select(CommissionRule).where(
                CommissionRule.tenant_id == user.tenant_id,
                CommissionRule.supplier_id == order.proposal.supplier_id,
                CommissionRule.is_active.is_(True),
            ).order_by(CommissionRule.created_at.desc())
        )
        if not rule:
            rule = db.scalar(
                select(CommissionRule).where(
                    CommissionRule.tenant_id == user.tenant_id,
                    CommissionRule.supplier_id.is_(None),
                    CommissionRule.is_active.is_(True),
                ).order_by(CommissionRule.created_at.desc())
            )
    if not rule:
        raise HTTPException(409, "No active commission rule available")

    financial = initialize_order_financial(db, user.tenant_id, order, rule)
    record_audit(
        db, user.tenant_id, user.id, "financial.snapshot_created", "order_financial", financial.id,
        {"order_id": str(order.id), "commission": str(financial.commission_amount)},
    )
    record_event(
        db, user.tenant_id, f"order:{order.id}:financial-initialized", "CommissionGenerated",
        "order", order.id,
        {"financial_id": str(financial.id), "commission": str(financial.commission_amount)},
    )
    db.commit()
    db.refresh(financial)
    return financial


@router.get("/orders/{order_id}", response_model=OrderFinancialResponse)
def get_order_financial(order_id: str, user: CurrentUser, db: DbSession):
    financial = db.scalar(
        select(OrderFinancial).where(
            OrderFinancial.order_id == order_id,
            OrderFinancial.tenant_id == user.tenant_id,
        )
    )
    if not financial:
        raise HTTPException(404, "Financial snapshot not found")
    return financial


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, user: CurrentUser, db: DbSession):
    financial = db.scalar(
        select(OrderFinancial).where(
            OrderFinancial.order_id == payload.order_id,
            OrderFinancial.tenant_id == user.tenant_id,
        )
    )
    if not financial:
        raise HTTPException(409, "Initialize order financials before creating a payment")
    if payload.currency != financial.currency:
        raise HTTPException(422, "Payment currency does not match order currency")

    active_total = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.order_id == payload.order_id,
            Payment.tenant_id == user.tenant_id,
            Payment.status.in_(["pending", "authorized", "paid", "partially_refunded"]),
        )
    )
    if active_total + payload.amount > financial.gross_amount:
        raise HTTPException(422, "Payment total would exceed order gross amount")

    payment = Payment(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(payment)
    db.flush()
    record_event(
        db, user.tenant_id, f"payment:{payment.id}:created", "PaymentCreated",
        "payment", payment.id, {"order_id": str(payment.order_id), "amount": str(payment.amount)},
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.patch("/payments/{payment_id}", response_model=PaymentResponse)
def update_payment(payment_id: str, payload: PaymentUpdate, user: CurrentUser, db: DbSession):
    payment = db.scalar(
        select(Payment).where(Payment.id == payment_id, Payment.tenant_id == user.tenant_id)
    )
    if not payment:
        raise HTTPException(404, "Payment not found")
    if payment.status in {"refunded", "cancelled"}:
        raise HTTPException(409, "Payment is closed")
    allowed = {
        "pending": {"authorized", "paid", "failed", "cancelled"},
        "authorized": {"paid", "failed", "cancelled"},
        "paid": {"refunded", "partially_refunded"},
        "partially_refunded": {"refunded"},
        "failed": set(),
    }
    if (
        payload.status != payment.status
        and payload.status not in allowed.get(payment.status, set())
    ):
        raise HTTPException(409, "Invalid payment status transition")
    payment.status = payload.status
    if payload.provider_reference:
        payment.provider_reference = payload.provider_reference
    if payload.status == "paid":
        payment.paid_at = datetime.now(timezone.utc)
    record_event(
        db, user.tenant_id, f"payment:{payment.id}:status:{payload.status}", "PaymentStatusChanged",
        "payment", payment.id, {"status": payload.status},
    )
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/payments", response_model=list[PaymentResponse])
def list_payments(user: CurrentUser, db: DbSession):
    return db.scalars(
        select(Payment)
        .where(Payment.tenant_id == user.tenant_id)
        .order_by(Payment.created_at.desc())
    ).all()


@router.get("/settlements", response_model=list[SettlementResponse])
def list_settlements(user: CurrentUser, db: DbSession):
    return db.scalars(
        select(Settlement)
        .where(Settlement.tenant_id == user.tenant_id)
        .order_by(Settlement.created_at.desc())
    ).all()


@router.post("/settlements/{order_id}/pay", response_model=SettlementResponse)
def pay_settlement(order_id: str, user: CurrentUser, db: DbSession):
    settlement = db.scalar(
        select(Settlement).where(
            Settlement.order_id == order_id,
            Settlement.tenant_id == user.tenant_id,
        )
    )
    if not settlement:
        raise HTTPException(404, "Settlement not found")
    if settlement.status not in {"pending", "scheduled"}:
        raise HTTPException(409, "Settlement cannot be paid from its current status")
    settlement.status = "paid"
    settlement.paid_at = datetime.now(timezone.utc)
    record_event(
        db, user.tenant_id, f"settlement:{settlement.id}:paid", "SettlementPaid",
        "settlement",
        settlement.id,
        {"order_id": str(settlement.order_id), "amount": str(settlement.amount)},
    )
    db.commit()
    db.refresh(settlement)
    return settlement


@router.post("/settlements/{order_id}/reconcile", response_model=SettlementResponse)
def reconcile_settlement(order_id: str, user: CurrentUser, db: DbSession):
    settlement = db.scalar(
        select(Settlement).where(
            Settlement.order_id == order_id,
            Settlement.tenant_id == user.tenant_id,
        )
    )
    if not settlement:
        raise HTTPException(404, "Settlement not found")
    if settlement.status != "paid":
        raise HTTPException(409, "Settlement must be paid before reconciliation")
    settlement.status = "reconciled"
    settlement.reconciled_at = datetime.now(timezone.utc)
    record_event(
        db, user.tenant_id, f"settlement:{settlement.id}:reconciled", "ReconciliationCompleted",
        "settlement", settlement.id, {"order_id": str(settlement.order_id)},
    )
    db.commit()
    db.refresh(settlement)
    return settlement
