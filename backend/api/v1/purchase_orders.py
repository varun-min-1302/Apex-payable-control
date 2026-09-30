from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

from backend.api.deps import get_db, get_current_user
from backend.database.models.identity import User
from backend.database.models.procurement import PurchaseOrder, PurchaseOrderItem
from backend.api.schemas.procurement_schemas import PurchaseOrderOut, PurchaseOrderItemOut

router = APIRouter(prefix="/purchase-orders", tags=["Procurement - Purchase Orders"])

@router.get("", response_model=list[PurchaseOrderOut])
def list_purchase_orders(
    vendor_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List purchase orders for the active tenant."""
    stmt = (
        select(PurchaseOrder)
        .where(PurchaseOrder.tenant_id == current_user.tenant_id)
        .options(selectinload(PurchaseOrder.items))
        .order_by(desc(PurchaseOrder.po_date))
    )

    if vendor_id:
        stmt = stmt.where(PurchaseOrder.vendor_id == vendor_id)
    if status_filter:
        stmt = stmt.where(PurchaseOrder.status == status_filter.upper())

    stmt = stmt.offset(offset).limit(limit)
    orders = db.execute(stmt).scalars().all()

    result = []
    for po in orders:
        item_outs = [PurchaseOrderItemOut.model_validate(it) for it in po.items]
        po_out = PurchaseOrderOut(
            id=po.id,
            tenant_id=po.tenant_id,
            vendor_id=po.vendor_id,
            po_number=po.po_number,
            po_date=po.po_date,
            status=po.status,
            currency=po.currency,
            subtotal=po.subtotal,
            discount_total=po.discount_total,
            tax_total=po.tax_total,
            grand_total=po.grand_total,
            payment_terms_days=po.payment_terms_days,
            approved_at=po.approved_at,
            items=item_outs
        )
        result.append(po_out)

    return result

@router.get("/{po_id}", response_model=PurchaseOrderOut)
def get_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a purchase order by ID including line items."""
    stmt = (
        select(PurchaseOrder)
        .where(PurchaseOrder.tenant_id == current_user.tenant_id, PurchaseOrder.id == po_id)
        .options(selectinload(PurchaseOrder.items))
    )
    po = db.execute(stmt).scalars().first()
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found.")

    item_outs = [PurchaseOrderItemOut.model_validate(it) for it in po.items]
    return PurchaseOrderOut(
        id=po.id,
        tenant_id=po.tenant_id,
        vendor_id=po.vendor_id,
        po_number=po.po_number,
        po_date=po.po_date,
        status=po.status,
        currency=po.currency,
        subtotal=po.subtotal,
        discount_total=po.discount_total,
        tax_total=po.tax_total,
        grand_total=po.grand_total,
        payment_terms_days=po.payment_terms_days,
        approved_at=po.approved_at,
        items=item_outs
    )
