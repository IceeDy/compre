from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import Customer, Supplier, SupplierCustomerRegistration
from app.schemas.supplier_registration import (
    SupplierRegistrationCreate,
    SupplierRegistrationResponse,
    SupplierRegistrationUpdate,
)
from app.services.governance import record_audit, record_event

router = APIRouter(prefix="/supplier-registrations", tags=["supplier-registrations"])


@router.post("", response_model=SupplierRegistrationResponse, status_code=status.HTTP_201_CREATED)
def create_registration(
    payload: SupplierRegistrationCreate,
    user: CurrentUser,
    db: DbSession,
):
    supplier = db.scalar(
        select(Supplier).where(
            Supplier.id == payload.supplier_id,
            Supplier.tenant_id == user.tenant_id,
            Supplier.is_active.is_(True),
        )
    )
    customer = db.scalar(
        select(Customer).where(
            Customer.id == payload.customer_id,
            Customer.tenant_id == user.tenant_id,
            Customer.is_active.is_(True),
        )
    )
    if not supplier or not customer:
        raise HTTPException(404, "Supplier or customer not found")

    existing = db.scalar(
        select(SupplierCustomerRegistration).where(
            SupplierCustomerRegistration.tenant_id == user.tenant_id,
            SupplierCustomerRegistration.supplier_id == supplier.id,
            SupplierCustomerRegistration.customer_id == customer.id,
        )
    )
    if existing:
        raise HTTPException(409, "Registration workflow already exists")

    registration = SupplierCustomerRegistration(
        tenant_id=user.tenant_id,
        supplier_id=supplier.id,
        customer_id=customer.id,
        status="requested",
        metadata={"requested_fields": payload.requested_fields},
    )
    db.add(registration)
    db.flush()

    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="supplier.registration_requested",
        entity_type="supplier_customer_registration",
        entity_id=registration.id,
        metadata={"supplier_id": str(supplier.id), "customer_id": str(customer.id)},
    )
    record_event(
        db,
        tenant_id=user.tenant_id,
        event_key=f"supplier-registration:{registration.id}:requested",
        event_type="SupplierRegistrationRequested",
        aggregate_type="supplier_customer_registration",
        aggregate_id=registration.id,
        payload={"supplier_id": str(supplier.id), "customer_id": str(customer.id)},
    )
    db.commit()
    db.refresh(registration)
    return registration


@router.get("", response_model=list[SupplierRegistrationResponse])
def list_registrations(user: CurrentUser, db: DbSession):
    return db.scalars(
        select(SupplierCustomerRegistration)
        .where(SupplierCustomerRegistration.tenant_id == user.tenant_id)
        .order_by(SupplierCustomerRegistration.requested_at.desc())
    ).all()


@router.patch("/{registration_id}", response_model=SupplierRegistrationResponse)
def update_registration(
    registration_id: str,
    payload: SupplierRegistrationUpdate,
    user: CurrentUser,
    db: DbSession,
):
    registration = db.scalar(
        select(SupplierCustomerRegistration).where(
            SupplierCustomerRegistration.id == registration_id,
            SupplierCustomerRegistration.tenant_id == user.tenant_id,
        )
    )
    if not registration:
        raise HTTPException(404, "Registration workflow not found")

    if registration.status in {"approved", "rejected"}:
        raise HTTPException(409, "Registration workflow is already finalized")

    if payload.status == "rejected" and not payload.rejection_reason:
        raise HTTPException(400, "Rejection reason is required")

    registration.status = payload.status
    registration.external_reference = payload.external_reference
    registration.rejection_reason = payload.rejection_reason
    registration.reviewed_at = datetime.now(timezone.utc)
    db.flush()

    event_type = (
        "SupplierRegistrationApproved"
        if payload.status == "approved"
        else "SupplierRegistrationRejected"
        if payload.status == "rejected"
        else "SupplierRegistrationUnderReview"
    )
    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action=f"supplier.registration_{payload.status}",
        entity_type="supplier_customer_registration",
        entity_id=registration.id,
        metadata={"supplier_id": str(registration.supplier_id), "customer_id": str(registration.customer_id)},
    )
    record_event(
        db,
        tenant_id=user.tenant_id,
        event_key=f"supplier-registration:{registration.id}:{payload.status}",
        event_type=event_type,
        aggregate_type="supplier_customer_registration",
        aggregate_id=registration.id,
        payload={
            "supplier_id": str(registration.supplier_id),
            "customer_id": str(registration.customer_id),
        },
    )
    db.commit()
    db.refresh(registration)
    return registration
