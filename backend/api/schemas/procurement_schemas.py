from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class PurchaseOrderItemOut(BaseModel):
    id: UUID
    line_number: int
    product_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True

class PurchaseOrderOut(BaseModel):
    id: UUID
    tenant_id: UUID
    vendor_id: UUID
    po_number: str
    po_date: date
    status: str
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    payment_terms_days: int
    approved_at: Optional[datetime] = None
    items: list[PurchaseOrderItemOut] = []

    class Config:
        from_attributes = True

class GoodsReceiptItemOut(BaseModel):
    id: UUID
    purchase_order_item_id: UUID
    received_quantity: Decimal
    accepted_quantity: Decimal
    rejected_quantity: Decimal
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class GoodsReceiptOut(BaseModel):
    id: UUID
    tenant_id: UUID
    purchase_order_id: UUID
    receipt_number: str
    received_date: date
    status: str
    notes: Optional[str] = None
    items: list[GoodsReceiptItemOut] = []

    class Config:
        from_attributes = True
