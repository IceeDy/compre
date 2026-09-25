from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import Order, SupplierOrder
from app.schemas.supplier_order import SupplierOrderResponse, SupplierOrderUpdate
from app.services.governance import record_audit, record_event

router = APIRouter(prefix="/supplier-orders", tags=["supplier-orders"])

_ALLOWED_TRANSITIONS = {
    "sent": {"confirmed", "rejected", "cancelled"},
    "confirmed": {"preparing", "cancelled"},
    "preparing": {"shipped", "cancelled"},
    "shipped": {"delivered"},
}


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

    supplier_order = SupplierOrder(
        tenant_id=user.tenant_id,
        order_id=order.id,
        supplier_id=db.scalar(
            select(Order.proposal_id).where(
                Order.id == order.id,
                Order.tenant_id == user.tenant_id,
            )
        ),
        status="sent",
    )
