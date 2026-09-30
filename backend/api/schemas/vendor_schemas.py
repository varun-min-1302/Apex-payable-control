from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel

class VendorOut(BaseModel):
    id: UUID
    tenant_id: UUID
    vendor_code: str
    legal_name: str
    display_name: Optional[str] = None
    tax_identifier: str
    currency: str
    payment_terms_days: int
    status: str
    risk_status: str
    bank_account_last4: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class VendorDetailOut(VendorOut):
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    total_invoices_count: int = 0
    open_invoices_count: int = 0
