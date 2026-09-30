import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field

class ExtractedField(BaseModel):
    """
    Representation of an individual field extracted from an invoice,
    retaining evidence, page reference, confidence, and source attribution.
    """
    value: Optional[str] = None
    evidence: Optional[str] = None
    page: int = 1
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = "GEMINI"

    class Config:
        frozen = False

class ExtractedLineItem(BaseModel):
    """Line item with itemized evidence and confidence."""
    line_number: int = 1
    description: ExtractedField = Field(default_factory=lambda: ExtractedField(source="GEMINI"))
    quantity: ExtractedField = Field(default_factory=lambda: ExtractedField(source="GEMINI"))
    unit_price: ExtractedField = Field(default_factory=lambda: ExtractedField(source="GEMINI"))
    tax_rate: ExtractedField = Field(default_factory=lambda: ExtractedField(source="GEMINI"))
    line_total: ExtractedField = Field(default_factory=lambda: ExtractedField(source="GEMINI"))

class GeminiExtractionResponse(BaseModel):
    """Strict schema for Gemini structured output."""
    invoice_number: Optional[ExtractedField] = None
    invoice_date: Optional[ExtractedField] = None
    due_date: Optional[ExtractedField] = None
    vendor_name: Optional[ExtractedField] = None
    vendor_tax_id: Optional[ExtractedField] = None
    purchase_order_number: Optional[ExtractedField] = None
    currency: Optional[ExtractedField] = None
    payment_terms_days: Optional[ExtractedField] = None
    subtotal: Optional[ExtractedField] = None
    tax_total: Optional[ExtractedField] = None
    grand_total: Optional[ExtractedField] = None
    line_items: List[ExtractedLineItem] = Field(default_factory=list)

class VendorMatchInfo(BaseModel):
    matched: bool = False
    vendor_id: Optional[uuid.UUID] = None
    vendor_name: Optional[str] = None
    vendor_code: Optional[str] = None
    tax_identifier: Optional[str] = None
    match_method: str = "NO_MATCH"  # TAX_ID, EXACT_NAME, FUZZY_NAME, NO_MATCH
    match_score: float = 0.0

class ExtractionResult(BaseModel):
    """Canonical internal result from any InvoiceExtractor."""
    document_id: Optional[uuid.UUID] = None
    provider: str = "gemini"
    model_name: str = "gemini-2.5-flash"
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    field_confidences: Dict[str, float] = Field(default_factory=dict)
    overall_confidence: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    vendor_match: Optional[VendorMatchInfo] = None
    arithmetic_valid: bool = True
    subtotal: Optional[Decimal] = None
    tax_total: Optional[Decimal] = None
    grand_total: Optional[Decimal] = None

class InvoiceDraftResponse(BaseModel):
    """API response model for an InvoiceDraft."""
    draft_id: uuid.UUID
    tenant_id: uuid.UUID
    document_id: uuid.UUID
    status: str
    overall_confidence: Optional[float] = None
    field_confidences: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    vendor_match: Optional[Dict[str, Any]] = None
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    confirmed_invoice_id: Optional[uuid.UUID] = None
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InvoiceDraftUpdate(BaseModel):
    """Payload for human reviewer updating draft fields before confirmation."""
    model_config = {"extra": "allow"}
    extracted_data: Optional[Dict[str, Any]] = None
    vendor_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None

class ConfirmDraftResponse(BaseModel):
    """Response returned upon confirming draft and triggering controls."""
    draft_id: uuid.UUID
    invoice_id: uuid.UUID
    invoice_number: str
    status: str
    control_run_id: Optional[uuid.UUID] = None
    control_run_status: Optional[str] = None
    passed_controls: int = 0
    failed_controls: int = 0
    warning_controls: int = 0
    exception_count: int = 0
    risk_signal_count: int = 0
    message: str
