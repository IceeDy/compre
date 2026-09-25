from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models import Order, OrderItem, Proposal, Quote, QuoteItem
from app.schemas.commercial import OrderResponse
from app.services.governance import record_audit, record_event

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/from-proposal/{proposal_id}", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(proposal_id: str, user: CurrentUser, db: DbSession):
    proposal = db.scalar(
        select(Proposal).options(selectinload(Proposal.items), selectinload(Proposal.quote))
        .where(Proposal.id == proposal_id, Proposal.tenant_id == user.tenant_id)
    )
    if not proposal:
        raise HTTPException(404, "Proposal not found")
    if proposal.status != "received":
        raise HTTPException(409, "Proposal cannot be converted from its current status")
    order = Order(
        tenant_id=user.tenant_id,
        customer_id=proposal.quote.customer_id,
        proposal_id=proposal.id,
        total=proposal.total,
        status="pending",
    )
    for item in proposal.items:
        quote_item = db.get(QuoteItem, item.quote_item_id)
        order.items.append(OrderItem(
            product_id=quote_item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item.total,
        ))
    proposal.status = "accepted"
    proposal.quote.status = "approved"
    db.add(order)
    db.flush()
    record_audit(
        db, tenant_id=user.tenant_id, actor_user_id=user.id,
        action="order.created", entity_type="order", entity_id=order.id,
        metadata={"proposal_id": str(proposal.id), "total": str(order.total)},
    )
    record_event(
        db, tenant_id=user.tenant_id, event_key=f"order:{order.id}:created",
        event_type="OrderCreated", aggregate_type="order", aggregate_id=order.id,
        payload={"proposal_id": str(proposal.id), "customer_id": str(order.customer_id), "total": str(order.total)},
    )
    db.commit(); db.refresh(order)
    return order


@router.get("", response_model=list[OrderResponse])
def list_orders(user: CurrentUser, db: DbSession):
    return db.scalars(select(Order).where(Order.tenant_id == user.tenant_id).order_by(Order.created_at.desc())).all()
