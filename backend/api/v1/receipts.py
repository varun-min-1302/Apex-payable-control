from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

from backend.api.deps import get_db, get_current_user
from backend.database.models.identity import User
from backend.database.models.procurement import GoodsReceipt, GoodsReceiptItem
from backend.api.schemas.procurement_schemas import GoodsReceiptOut, GoodsReceiptItemOut

router = APIRouter(prefix="/receipts", tags=["Procurement - Goods Receipts"])

@router.get("", response_model=list[GoodsReceiptOut])
def list_goods_receipts(
    purchase_order_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List warehouse receiving receipts for the active tenant."""
    stmt = (
        select(GoodsReceipt)
        .where(GoodsReceipt.tenant_id == current_user.tenant_id)
        .options(selectinload(GoodsReceipt.items))
        .order_by(desc(GoodsReceipt.received_date))
    )

    if purchase_order_id:
        stmt = stmt.where(GoodsReceipt.purchase_order_id == purchase_order_id)

    stmt = stmt.offset(offset).limit(limit)
    receipts = db.execute(stmt).scalars().all()

    result = []
    for gr in receipts:
        item_outs = [GoodsReceiptItemOut.model_validate(it) for it in gr.items]
        result.append(
            GoodsReceiptOut(
                id=gr.id,
                tenant_id=gr.tenant_id,
                purchase_order_id=gr.purchase_order_id,
                receipt_number=gr.receipt_number,
                received_date=gr.received_date,
                status=gr.status,
                notes=gr.notes,
                items=item_outs
            )
        )
    return result

@router.get("/{receipt_id}", response_model=GoodsReceiptOut)
def get_goods_receipt(
    receipt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve goods receipt by ID including line item receipt quantities."""
    stmt = (
        select(GoodsReceipt)
        .where(GoodsReceipt.tenant_id == current_user.tenant_id, GoodsReceipt.id == receipt_id)
        .options(selectinload(GoodsReceipt.items))
    )
    gr = db.execute(stmt).scalars().first()
    if not gr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt not found.")

    item_outs = [GoodsReceiptItemOut.model_validate(it) for it in gr.items]
    return GoodsReceiptOut(
        id=gr.id,
        tenant_id=gr.tenant_id,
        purchase_order_id=gr.purchase_order_id,
        receipt_number=gr.receipt_number,
        received_date=gr.received_date,
        status=gr.status,
        notes=gr.notes,
        items=item_outs
    )
