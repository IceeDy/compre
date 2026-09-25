from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import Order, Proposal, SupplierOrder
from app.schemas.supplier_order import SupplierOrderResponse, SupplierOrderUpdate
from app.services.governance import record_audit, record_event

router = APIRouter(prefix="/supplier-orders", tags=["supplier-orders"])

_ALLOWED_TRANSITIONS = {
    "sent": {"confirmed", "rejected", "cancelled"},
    "confirmed": {"preparing", "cancelled"},
    "preparing": {"shipped", "cancelled"},
    "shipped": {"delivered"},
}


def _event_type(status_value: str) -> str:
    return {
        "confirmed": "SupplierOrderConfirmed",
        "rejected": "SupplierOrderRejected",
        "preparing": "SupplierOrderPreparing",
        "shipped": "SupplierOrderShipped",
        "delivered": "DeliveryCompleted",
        "cancelled": "SupplierOrderCancelled",
    }[status_value]


@router.post(
    "/from-order/{order_id}",
    response_model=SupplierOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier_order(order_id: str, user: CurrentUser, db: DbSession):
    order = db.scalar(
        select(Order).where(
            Order.id == order_id,
            Order.tenant_id == user.tenant_id,
        )
    )
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != "released":
        raise HTTPException(409, "Only released orders can be sent to a supplier")

    existing = db.scalar(
        select(SupplierOrder).where(
            SupplierOrder.tenant_id == user.tenant_id,
            SupplierOrder.order_id == order.id,
        )
    )
    if existing:
        raise HTTPException(409, "Supplier order already exists")

    proposal = db.scalar(
        select(Proposal).where(
            Proposal.id == order.proposal_id,
            Proposal.tenant_id == user.tenant_id,
        )
    )
    if not proposal:
        raise HTTPException(404, "Order proposal not found")

    supplier_order = SupplierOrder(
        tenant_id=user.tenant_id,
        order_id=order.id,
        supplier_id=proposal.supplier_id,
        status="sent",
    )
    db.add(supplier_order)
    db.flush()

    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="supplier_order.sent",
        entity_type="supplier_order",
        entity_id=supplier_order.id,
        metadata={
            "order_id": str(order.id),
            "supplier_id": str(supplier_order.supplier_id),
        },
    )
    record_event(
        db,
        tenant_id=user.tenant_id,
        event_key=f"supplier-order:{supplier_order.id}:sent",
        event_type="SupplierOrderSent",
        aggregate_type="supplier_order",
        aggregate_id=supplier_order.id,
        payload={
            "order_id": str(order.id),
            "supplier_id": str(supplier_order.supplier_id),
        },
    )
    db.commit()
    db.refresh(supplier_order)
    return supplier_order


@router.get("", response_model=list[SupplierOrderResponse])
def list_supplier_orders(user: CurrentUser, db: DbSession):
    return db.scalars(
        select(SupplierOrder)
        .where(SupplierOrder.tenant_id == user.tenant_id)
        .order_by(SupplierOrder.sent_at.desc())
    ).all()


@router.patch("/{supplier_order_id}", response_model=SupplierOrderResponse)
def update_supplier_order(
    supplier_order_id: str,
    payload: SupplierOrderUpdate,
    user: CurrentUser,
    db: DbSession,
):
    supplier_order = db.scalar(
        select(SupplierOrder).where(
            SupplierOrder.id == supplier_order_id,
            SupplierOrder.tenant_id == user.tenant_id,
        )
    )
    if not supplier_order:
        raise HTTPException(404, "Supplier order not found")

    allowed = _ALLOWED_TRANSITIONS.get(supplier_order.status, set())
    if payload.status not in allowed:
        raise HTTPException(
            409,
            f"Invalid supplier order transition: {supplier_order.status} -> {payload.status}",
        )

    if payload.status == "rejected" and not payload.rejection_reason:
        raise HTTPException(400, "Rejection reason is required")

    now = datetime.now(timezone.utc)
    supplier_order.status = payload.status
    supplier_order.external_reference = payload.external_reference
    supplier_order.rejection_reason = payload.rejection_reason

    if payload.status == "confirmed":
        supplier_order.confirmed_at = now
    elif payload.status == "shipped":
        supplier_order.shipped_at = now
    elif payload.status == "delivered":
        supplier_order.delivered_at = now

    db.flush()

    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action=f"supplier_order.{payload.status}",
        entity_type="supplier_order",
        entity_id=supplier_order.id,
        metadata={
            "order_id": str(supplier_order.order_id),
            "supplier_id": str(supplier_order.supplier_id),
            "external_reference": payload.external_reference,
        },
    )
    record_event(
        db,
        tenant_id=user.tenant_id,
        event_key=f"supplier-order:{supplier_order.id}:{payload.status}",
        event_type=_event_type(payload.status),
        aggregate_type="supplier_order",
        aggregate_id=supplier_order.id,
        payload={
            "order_id": str(supplier_order.order_id),
            "supplier_id": str(supplier_order.supplier_id),
            "status": payload.status,
        },
    )
    db.commit()
    db.refresh(supplier_order)
    return supplier_order
