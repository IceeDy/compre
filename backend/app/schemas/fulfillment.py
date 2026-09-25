from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ShipmentCreate(BaseModel):
    carrier: str | None = Field(default=None, max_length=120)
    tracking_number: str | None = Field(default=None, max_length=120)
    estimated_delivery_at: datetime | None = None


class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    supplier_order_id: UUID
    carrier: str | None
    tracking_number: str | None
    shipped_at: datetime
    estimated_delivery_at: datetime | None
    created_at: datetime


class DeliveryUpdate(BaseModel):
    status: str = Field(pattern=r"^(delivered|failed)$")
    recipient_name: str | None = Field(default=None, max_length=160)
    proof_reference: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)


class DeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    shipment_id: UUID
    status: str
    delivered_at: datetime | None
    recipient_name: str | None
    proof_reference: str | None
    notes: str | None
    created_at: datetime
