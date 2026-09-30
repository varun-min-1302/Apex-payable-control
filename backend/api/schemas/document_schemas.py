from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class InvoiceIntakeResponse(BaseModel):
    document_id: UUID
    tenant_id: UUID
    filename: str
    size_bytes: int
    mime_type: str
    status: str
    duplicate: bool = False
    existing_document_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    created_at: datetime
    message: Optional[str] = None

    class Config:
        from_attributes = True

class InvoiceDocumentSummaryOut(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_id: Optional[UUID] = None
    original_filename: str
    sanitized_filename: str
    mime_type: str
    file_size_bytes: int
    status: str
    source: str
    uploaded_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
