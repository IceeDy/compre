from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SupplierOrderUpdate(BaseModel):
    status: str = Field(pattern=r"^(confirmed|rejected|preparing|shipped|delivered|cancelled)$")
    external_reference: str | None = Field(default=None, max_length=120)
    rejection_reason: str | None = Field(default=None, max_length=500)


class SupplierOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    order_id: UUID
    supplier_id: UUID
    status: str
    external_reference: str | None
    rejection_reason: str | None
    sent_at: datetime
    confirmed_at: datetime | None
    shipped_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime
