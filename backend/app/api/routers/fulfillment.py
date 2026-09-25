from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import Delivery, Shipment, SupplierOrder
from app.schemas.fulfillment import (
    DeliveryResponse,
    DeliveryUpdate,
    ShipmentCreate,
    ShipmentResponse,
)
from app.services.governance import record_audit, record_event

router = APIRouter(prefix="/fulfillment", tags=["fulfillment"])


@router.post(
    "/supplier-orders/{supplier_order_id}/shipment",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shipment(
    supplier_order_id: str,
    payload: ShipmentCreate,
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
    if supplier_order.status != "shipped":
        raise HTTPException(409, "Shipment can only be created for a shipped supplier order")

    existing = db.scalar(select(Shipment).where(Shipment.supplier_order_id == supplier_order.id))
    if existing:
        raise HTTPException(409, "Shipment already exists")

    shipment = Shipment(
        tenant_id=user.tenant_id,
        supplier_order_id=supplier_order.id,
        carrier=payload.carrier,
        tracking_number=payload.tracking_number,
        estimated_delivery_at=payload.estimated_delivery_at,
    )
    db.add(shipment)
    db.flush()

    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="shipment.created",
        entity_type="shipment",
        entity_id=shipment.id,
        metadata={
            "supplier_order_id": str(supplier_order.id),
            "carrier": payload.carrier,
            "tracking_number": payload.tracking_number,
        },
    )
    record_event(
        db,
        tenant_id=user.tenant_id,
        event_key=f"shipment:{shipment.id}:created",
        event_type="ShipmentCreated",
        aggregate_type="shipment",
        aggregate_id=shipment.id,
        payload={"supplier_order_id": str(supplier_order.id)},
    )
    db.commit()
    db.refresh(shipment)
    return shipment


@router.post(
    "/shipments/{shipment_id}/delivery",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_delivery(
    shipment_id: str,
    user: CurrentUser,
    db: DbSession,
):
    shipment = db.scalar(
        select(Shipment).where(
            Shipment.id == shipment_id,
            Shipment.tenant_id == user.tenant_id,
        )
    )
    if not shipment:
        raise HTTPException(404, "Shipment not found")
    if shipment.delivery:
        raise HTTPException(409, "Delivery record already exists")

    delivery = Delivery(
        tenant_id=user.tenant_id,
        shipment_id=shipment.id,
        status="pending",
    )
    db.add(delivery)
    db.flush()

    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="delivery.created",
        entity_type="delivery",
        entity_id=delivery.id,
        metadata={"shipment_id": str(shipment.id)},
    )
    record_event(
        db,
        tenant_id=user.tenant_id,
        event_key=f"delivery:{delivery.id}:created",
        event_type="DeliveryCreated",
        aggregate_type="delivery",
        aggregate_id=delivery.id,
        payload={"shipment_id": str(shipment.id)},
    )
    db.commit()
    db.refresh(delivery)
    return delivery


@router.patch("/deliveries/{delivery_id}", response_model=DeliveryResponse)
def update_delivery(
    delivery_id: str,
    payload: DeliveryUpdate,
    user: CurrentUser,
    db: DbSession,
):
    delivery = db.scalar(
        select(Delivery).where(
            Delivery.id == delivery_id,
            Delivery.tenant_id == user.tenant_id,
        )
    )
    if not delivery:
        raise HTTPException(404, "Delivery not found")
    if delivery.status != "pending":
        raise HTTPException(409, "Delivery is already finalized")

    if payload.status == "delivered" and not payload.recipient_name:
        raise HTTPException(400, "Recipient name is required for delivered status")

    delivery.status = payload.status
    delivery.recipient_name = payload.recipient_name
    delivery.proof_reference = payload.proof_reference
    delivery.notes = payload.notes

    if payload.status == "delivered":
        delivery.delivered_at = datetime.now(timezone.utc)

    db.flush()
    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action=f"delivery.{payload.status}",
        entity_type="delivery",
        entity_id=delivery.id,
        metadata={"shipment_id": str(delivery.shipment_id)},
    )
    record_event(
        db,
        tenant_id=user.tenant_id,
        event_key=f"delivery:{delivery.id}:{payload.status}",
        event_type="DeliveryCompleted" if payload.status == "delivered" else "DeliveryFailed",
        aggregate_type="delivery",
        aggregate_id=delivery.id,
        payload={"shipment_id": str(delivery.shipment_id), "status": payload.status},
    )
    db.commit()
    db.refresh(delivery)
    return delivery
