from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from backend.database.models.procurement import PurchaseOrder, PurchaseOrderItem

class PurchaseOrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, tenant_id: UUID, po_id: UUID) -> Optional[PurchaseOrder]:
        """Fetch purchase order with its line items eagerly loaded."""
        stmt = (
            select(PurchaseOrder)
            .where(PurchaseOrder.tenant_id == tenant_id, PurchaseOrder.id == po_id)
            .options(selectinload(PurchaseOrder.items))
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_number(self, tenant_id: UUID, po_number: str) -> Optional[PurchaseOrder]:
        """Fetch purchase order by PO number with its line items."""
        stmt = (
            select(PurchaseOrder)
            .where(PurchaseOrder.tenant_id == tenant_id, PurchaseOrder.po_number == po_number.strip())
            .options(selectinload(PurchaseOrder.items))
        )
        return self.session.execute(stmt).scalar_one_or_none()
