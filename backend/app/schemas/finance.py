from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommissionRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    rate_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    fixed_amount: Decimal = Field(default=Decimal("0"), ge=0)
    supplier_id: UUID | None = None


class CommissionRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    rate_percent: Decimal
    fixed_amount: Decimal
    supplier_id: UUID | None
    is_active: bool
    created_at: datetime


class OrderFinancialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    order_id: UUID
    gross_amount: Decimal
    commission_rate: Decimal
    commission_fixed_amount: Decimal
    commission_amount: Decimal
    supplier_net_amount: Decimal
    currency: str
    status: str
    created_at: datetime


class FinancialInitializeRequest(BaseModel):
    commission_rule_id: UUID | None = None


class PaymentCreate(BaseModel):
    order_id: UUID
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    flow: str = Field(pattern=r"^(customer_to_platform|customer_to_supplier)$")
    method: str = Field(min_length=1, max_length=40)
    provider_reference: str | None = Field(default=None, max_length=160)


class PaymentUpdate(BaseModel):
    status: str = Field(pattern=r"^(pending|authorized|paid|failed|cancelled|refunded|partially_refunded)$")
    provider_reference: str | None = Field(default=None, max_length=160)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    order_id: UUID
    amount: Decimal
    currency: str
    flow: str
    method: str
    status: str
    provider_reference: str | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SettlementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    order_id: UUID
    supplier_id: UUID
    financial_id: UUID
    amount: Decimal
    currency: str
    status: str
    provider_reference: str | None
    scheduled_at: datetime | None
    paid_at: datetime | None
    reconciled_at: datetime | None
    created_at: datetime
