from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ExceptionOut(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    control_result_id: Optional[UUID] = None
    exception_code: str
    title: str
    description: str
    severity: str
    status: str
    assigned_to: Optional[UUID] = None
    assigned_to_name: Optional[str] = None
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    resolution_reason: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ExceptionResolveRequest(BaseModel):
    action: str = "RESOLVE"  # "RESOLVE" or "WAIVE"
    reason: str
