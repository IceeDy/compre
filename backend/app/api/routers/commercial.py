from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models import Customer, Product, Proposal, ProposalItem, Quote, QuoteItem, QuoteSupplierRequest, Supplier
from app.schemas.quote_engine import QuoteComparisonResponse, SupplierRequestCreate, SupplierRequestResponse
from app.schemas.commercial import (
    CustomerCreate, CustomerResponse, ProductCreate, ProductResponse, ProposalCreate, ProposalResponse,
    QuoteCreate, QuoteResponse, SupplierCreate, SupplierResponse,
)

router = APIRouter(prefix="/commercial", tags=["commercial"])


@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, user: CurrentUser, db: DbSession):
    obj = Customer(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/customers", response_model=list[CustomerResponse])
def list_customers(user: CurrentUser, db: DbSession):
    return db.scalars(select(Customer).where(Customer.tenant_id == user.tenant_id).order_by(Customer.name)).all()


@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, user: CurrentUser, db: DbSession):
    obj = Supplier(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/suppliers", response_model=list[SupplierResponse])
def list_suppliers(user: CurrentUser, db: DbSession):
    return db.scalars(select(Supplier).where(Supplier.tenant_id == user.tenant_id).order_by(Supplier.name)).all()


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, user: CurrentUser, db: DbSession):
    obj = Product(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/products", response_model=list[ProductResponse])
def list_products(user: CurrentUser, db: DbSession):
    return db.scalars(select(Product).where(Product.tenant_id == user.tenant_id).order_by(Product.name)).all()


@router.post("/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(payload: QuoteCreate, user: CurrentUser, db: DbSession):
    customer = db.scalar(select(Customer).where(Customer.id == payload.customer_id, Customer.tenant_id == user.tenant_id))
    if not customer:
        raise HTTPException(404, "Customer not found")
    product_ids = {item.product_id for item in payload.items}
    products = db.scalars(select(Product).where(Product.id.in_(product_ids), Product.tenant_id == user.tenant_id)).all()
    if len(products) != len(product_ids):
        raise HTTPException(404, "One or more products not found")
    quote = Quote(tenant_id=user.tenant_id, customer_id=customer.id, notes=payload.notes)
    quote.items = [QuoteItem(**item.model_dump()) for item in payload.items]
    db.add(quote); db.commit(); db.refresh(quote)
    return db.scalar(select(Quote).options(selectinload(Quote.items)).where(Quote.id == quote.id))


@router.get("/quotes", response_model=list[QuoteResponse])
def list_quotes(user: CurrentUser, db: DbSession):
    return db.scalars(
        select(Quote).options(selectinload(Quote.items))
        .where(Quote.tenant_id == user.tenant_id).order_by(Quote.created_at.desc())
    ).all()


@router.post("/proposals", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
def create_proposal(payload: ProposalCreate, user: CurrentUser, db: DbSession):
    quote = db.scalar(select(Quote).options(selectinload(Quote.items)).where(Quote.id == payload.quote_id, Quote.tenant_id == user.tenant_id))
    supplier = db.scalar(select(Supplier).where(Supplier.id == payload.supplier_id, Supplier.tenant_id == user.tenant_id))
    if not quote or not supplier:
        raise HTTPException(404, "Quote or supplier not found")
    valid_items = {item.id: item for item in quote.items}
    if any(item.quote_item_id not in valid_items for item in payload.items):
        raise HTTPException(400, "Proposal contains an item outside the quote")
    if len({item.quote_item_id for item in payload.items}) != len(payload.items):
        raise HTTPException(400, "Proposal contains duplicate quote items")
    if any(item.quantity != valid_items[item.quote_item_id].quantity for item in payload.items):
        raise HTTPException(400, "Proposal quantity must match the requested quantity")
    proposal = Proposal(tenant_id=user.tenant_id, quote_id=quote.id, supplier_id=supplier.id)
    proposal.items = [
        ProposalItem(
            quote_item_id=item.quote_item_id,
            unit_price=item.unit_price,
            quantity=item.quantity,
            total=item.unit_price * item.quantity,
        ) for item in payload.items
    ]
    proposal.total = sum((item.total for item in proposal.items), Decimal("0"))
    request = db.scalar(
        select(QuoteSupplierRequest).where(
            QuoteSupplierRequest.quote_id == quote.id,
            QuoteSupplierRequest.supplier_id == supplier.id,
            QuoteSupplierRequest.tenant_id == user.tenant_id,
        )
    )
    if request:
        request.status = "responded"
        request.responded_at = datetime.now(timezone.utc)
    db.add(proposal); db.commit(); db.refresh(proposal)
    return db.scalar(select(Proposal).options(selectinload(Proposal.items)).where(Proposal.id == proposal.id))


@router.post("/quotes/{quote_id}/submit", response_model=QuoteResponse)
def submit_quote(quote_id: str, user: CurrentUser, db: DbSession):
    quote = db.scalar(select(Quote).options(selectinload(Quote.items)).where(Quote.id == quote_id, Quote.tenant_id == user.tenant_id))
    if not quote:
        raise HTTPException(404, "Quote not found")
    if quote.status != "draft":
        raise HTTPException(409, "Quote cannot be submitted from its current status")
    quote.status = "submitted"
    db.commit(); db.refresh(quote)
    return quote


@router.post("/quotes/{quote_id}/supplier-requests", response_model=list[SupplierRequestResponse])
def request_supplier_quotes(
    quote_id: str,
    payload: SupplierRequestCreate,
    user: CurrentUser,
    db: DbSession,
):
    quote = db.scalar(
        select(Quote).where(Quote.id == quote_id, Quote.tenant_id == user.tenant_id)
    )
    if not quote:
        raise HTTPException(404, "Quote not found")

    suppliers = db.scalars(
        select(Supplier).where(
            Supplier.id.in_(payload.supplier_ids),
            Supplier.tenant_id == user.tenant_id,
            Supplier.is_active.is_(True),
        )
    ).all()
    if len(suppliers) != len(set(payload.supplier_ids)):
        raise HTTPException(404, "One or more suppliers not found")

    existing = set(
        db.scalars(
            select(QuoteSupplierRequest.supplier_id).where(
                QuoteSupplierRequest.quote_id == quote.id,
                QuoteSupplierRequest.tenant_id == user.tenant_id,
            )
        ).all()
    )
    created = []
    for supplier in suppliers:
        if supplier.id in existing:
            continue
        created.append(
            QuoteSupplierRequest(
                tenant_id=user.tenant_id,
                quote_id=quote.id,
                supplier_id=supplier.id,
                status="requested",
            )
        )
    db.add_all(created)
    db.commit()
    return [{"supplier_id": row.supplier_id, "status": row.status} for row in created]


@router.get("/quotes/{quote_id}/comparison", response_model=QuoteComparisonResponse)
def compare_quote(quote_id: str, user: CurrentUser, db: DbSession):
    quote = db.scalar(
        select(Quote).options(selectinload(Quote.items)).where(
            Quote.id == quote_id, Quote.tenant_id == user.tenant_id
        )
    )
    if not quote:
        raise HTTPException(404, "Quote not found")

    from app.services.quote_engine import compare_quote as build_comparison

    return build_comparison(db, quote)
