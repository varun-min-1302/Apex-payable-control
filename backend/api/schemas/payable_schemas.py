from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class PaymentOut(BaseModel):
    id: UUID
    payable_id: UUID
    payment_reference: str
    payment_method: str
    amount: Decimal
    currency: str
    payment_date: date
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PayableLedgerOut(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    payable_number: str
    currency: str
    approved_amount: Decimal
    paid_amount: Decimal
    remaining_balance: Decimal
    due_date: date
    status: str
    approved_at: Optional[datetime] = None
    created_at: datetime
    payments: list[PaymentOut] = []

    class Config:
        from_attributes = True

class RecordPaymentRequest(BaseModel):
    amount: Decimal
    payment_reference: str
    payment_method: str = "NEFT"
