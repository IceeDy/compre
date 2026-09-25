from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SupplierRegistrationCreate(BaseModel):
    supplier_id: UUID
    customer_id: UUID
    metadata: dict = Field(default_factory=dict)


class SupplierRegistrationUpdate(BaseModel):
    status: str = Field(pattern="^(under_review|approved|rejected)$")
    external_reference: str | None = Field(default=None, max_length=120)
    rejection_reason: str | None = Field(default=None, max_length=500)


class SupplierRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    supplier_id: UUID
    customer_id: UUID
    status: str
    external_reference: str | None
    rejection_reason: str | None
    metadata: dict
    requested_at: datetime
    reviewed_at: datetime | None
