from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ApprovalOut(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_amount: Optional[Decimal] = None
    approval_policy_id: UUID
    policy_name: Optional[str] = None
    policy_tier: Optional[int] = None
    required_role: Optional[str] = None
    sequence_order: int
    approver_user_id: Optional[UUID] = None
    approver_name: Optional[str] = None
    status: str
    decision: Optional[str] = None
    comments: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ApprovalDecisionRequest(BaseModel):
    decision: str  # "APPROVE" or "REJECT"
    comments: Optional[str] = None

class ApprovalDecisionResponse(BaseModel):
    approval_id: UUID
    invoice_id: UUID
    decision: str
    invoice_status: str
    payable_created: bool
    payable_id: Optional[UUID] = None
    payable_number: Optional[str] = None
    message: str
