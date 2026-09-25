from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class SupplierRequestCreate(BaseModel):
    supplier_ids: list[UUID] = Field(min_length=1)


class SupplierRequestResponse(BaseModel):
    supplier_id: UUID
    status: str


class QuoteComparisonItem(BaseModel):
    quote_item_id: UUID
    product_id: UUID
    quantity: int
    target_price: Decimal | None
    best_unit_price: Decimal | None
    best_total: Decimal | None
    best_supplier_id: UUID | None
    savings_vs_target: Decimal | None


class SupplierComparison(BaseModel):
    supplier_id: UUID
    proposal_id: UUID | None
    status: str
    coverage: int
    coverage_percent: Decimal
    total: Decimal | None
    savings_vs_best_mix: Decimal | None


class QuoteComparisonResponse(BaseModel):
    quote_id: UUID
    item_count: int
    covered_item_count: int
    coverage_percent: Decimal
    best_mix_total: Decimal | None
    items: list[QuoteComparisonItem]
    suppliers: list[SupplierComparison]
