from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

class InvoiceItemOut(BaseModel):
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

class InvoiceRevisionOut(BaseModel):
    id: UUID
    revision_number: int
    invoice_number: str
    invoice_date: date
    due_date: date
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    vendor_name_as_submitted: Optional[str] = None
    vendor_tax_id_as_submitted: Optional[str] = None
    bank_account_last4: Optional[str] = None
    extraction_method: Optional[str] = None
    extraction_confidence: Optional[Decimal] = None
    submitted_at: datetime
    items: list[InvoiceItemOut] = []

    class Config:
        from_attributes = True

class InvoiceSummaryOut(BaseModel):
    id: UUID
    tenant_id: UUID
    vendor_id: UUID
    purchase_order_id: Optional[UUID] = None
    invoice_number: str
    invoice_date: date
    due_date: date
    currency: str
    status: str
    source_type: str
    document_hash: Optional[str] = None
    extraction_status: str
    extraction_confidence: Optional[Decimal] = None
    current_revision_id: Optional[UUID] = None
    grand_total: Optional[Decimal] = None
    vendor_name: Optional[str] = None
    risk_level: Optional[str] = None
    risk_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class InvoiceDetailOut(InvoiceSummaryOut):
    current_revision: Optional[InvoiceRevisionOut] = None
    revisions: list[InvoiceRevisionOut] = []
    active_exceptions_count: int = 0
    active_risk_signals_count: int = 0
    latest_control_run_status: Optional[str] = None

class InvoiceCreateItem(BaseModel):
    line_number: int
    product_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0.1800")
    discount_amount: Decimal = Decimal("0.00")

class InvoiceCreateRequest(BaseModel):
    vendor_id: UUID
    purchase_order_id: Optional[UUID] = None
    invoice_number: str
    invoice_date: date
    due_date: date
    currency: str = "INR"
    items: list[InvoiceCreateItem]
    raw_document_content: Optional[str] = None
