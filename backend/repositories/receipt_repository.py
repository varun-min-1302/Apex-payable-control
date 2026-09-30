from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from backend.database.models.procurement import GoodsReceipt, GoodsReceiptItem

class ReceiptRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_receipts_by_po_id(self, tenant_id: UUID, po_id: UUID) -> list[GoodsReceipt]:
        """Fetch all goods receipts for a purchase order with their items eagerly loaded."""
        stmt = (
            select(GoodsReceipt)
            .where(GoodsReceipt.tenant_id == tenant_id, GoodsReceipt.purchase_order_id == po_id)
            .options(selectinload(GoodsReceipt.items))
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_items_by_po_id(self, tenant_id: UUID, po_id: UUID) -> list[GoodsReceiptItem]:
        """Fetch all goods receipt items for a PO across all receipts."""
        stmt = (
            select(GoodsReceiptItem)
            .join(GoodsReceipt, GoodsReceiptItem.goods_receipt_id == GoodsReceipt.id)
            .where(GoodsReceipt.tenant_id == tenant_id, GoodsReceipt.purchase_order_id == po_id)
        )
        return list(self.session.execute(stmt).scalars().all())
