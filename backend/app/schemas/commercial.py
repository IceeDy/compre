from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    document: str | None = None
    email: str | None = None
    phone: str | None = None


class CustomerResponse(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    is_active: bool


class SupplierCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    document: str | None = None
    email: str | None = None
    phone: str | None = None


class SupplierResponse(SupplierCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    registration_status: str
    is_active: bool


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=2, max_length=220)
    unit: str = Field(default="UN", max_length=20)
    category: str | None = None
    reference_price: Decimal | None = None


class ProductResponse(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    is_active: bool


class QuoteItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)
    target_price: Decimal | None = Field(default=None, ge=0)


class QuoteCreate(BaseModel):
    customer_id: UUID
    notes: str | None = Field(default=None, max_length=1000)
    items: list[QuoteItemCreate] = Field(min_length=1)


class QuoteItemResponse(QuoteItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    status: str
    notes: str | None
    items: list[QuoteItemResponse]


class ProposalItemCreate(BaseModel):
    quote_item_id: UUID
    unit_price: Decimal = Field(ge=0)
    quantity: int = Field(gt=0)


class ProposalCreate(BaseModel):
    quote_id: UUID
    supplier_id: UUID
    items: list[ProposalItemCreate] = Field(min_length=1)


class ProposalItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    quote_item_id: UUID
    unit_price: Decimal
    quantity: int
    total: Decimal


class ProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    quote_id: UUID
    supplier_id: UUID
    status: str
    total: Decimal
    items: list[ProposalItemResponse]


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    proposal_id: UUID
    status: str
    total: Decimal
