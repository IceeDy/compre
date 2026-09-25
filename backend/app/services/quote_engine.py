from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Proposal, Quote, QuoteItem, QuoteSupplierRequest, Supplier


def compare_quote(db: Session, quote: Quote) -> dict:
    proposals = db.scalars(
        select(Proposal)
        .options(selectinload(Proposal.items))
        .where(Proposal.quote_id == quote.id, Proposal.tenant_id == quote.tenant_id)
    ).all()

    requests = db.scalars(
        select(QuoteSupplierRequest)
        .options(selectinload(QuoteSupplierRequest.supplier))
        .where(
            QuoteSupplierRequest.quote_id == quote.id,
            QuoteSupplierRequest.tenant_id == quote.tenant_id,
        )
    ).all()

    by_item: dict[UUID, list[tuple[Proposal, object]]] = {}
    proposal_by_supplier: dict[UUID, Proposal] = {}
    for proposal in proposals:
        proposal_by_supplier[proposal.supplier_id] = proposal
        for item in proposal.items:
            by_item.setdefault(item.quote_item_id, []).append((proposal, item))

    items = []
    best_mix_total = Decimal("0")
    covered = 0

    for quote_item in quote.items:
        candidates = by_item.get(quote_item.id, [])
        best = min(candidates, key=lambda pair: pair[1].unit_price, default=None)
        if best is None:
            best_unit = best_total = None
            best_supplier_id = None
        else:
            proposal, proposal_item = best
            best_unit = proposal_item.unit_price
            best_total = proposal_item.unit_price * quote_item.quantity
            best_supplier_id = proposal.supplier_id
            best_mix_total += best_total
            covered += 1

        target_savings = None
        if best_unit is not None and quote_item.target_price is not None:
            target_savings = (quote_item.target_price - best_unit) * quote_item.quantity

        items.append({
            "quote_item_id": quote_item.id,
            "product_id": quote_item.product_id,
            "quantity": quote_item.quantity,
            "target_price": quote_item.target_price,
            "best_unit_price": best_unit,
            "best_total": best_total,
            "best_supplier_id": best_supplier_id,
            "savings_vs_target": target_savings,
        })

    supplier_rows = []
    for request in requests:
        proposal = proposal_by_supplier.get(request.supplier_id)
        supplier_items = proposal.items if proposal else []
        supplier_coverage = len({item.quote_item_id for item in supplier_items})
        supplier_total = proposal.total if proposal else None
        status = "responded" if proposal else request.status
        supplier_rows.append({
            "supplier_id": request.supplier_id,
            "proposal_id": proposal.id if proposal else None,
            "status": status,
            "coverage": supplier_coverage,
            "coverage_percent": (
                Decimal(supplier_coverage * 100) / Decimal(len(quote.items))
                if quote.items else Decimal("0")
            ),
            "total": supplier_total,
            "savings_vs_best_mix": (
                supplier_total - best_mix_total
                if supplier_total is not None and covered == len(quote.items)
                else None
            ),
        })

    return {
        "quote_id": quote.id,
        "item_count": len(quote.items),
        "covered_item_count": covered,
        "coverage_percent": Decimal(covered * 100) / Decimal(len(quote.items)) if quote.items else Decimal("0"),
        "best_mix_total": best_mix_total if covered else None,
        "items": items,
        "suppliers": supplier_rows,
    }
