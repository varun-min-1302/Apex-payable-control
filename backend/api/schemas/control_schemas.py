from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

class ControlResultOut(BaseModel):
    id: UUID
    control_code: str
    category: str = Field(validation_alias="control_category")
    status: str
    severity: str
    expected_value: Optional[dict[str, Any]] = None
    actual_value: Optional[dict[str, Any]] = None
    variance_value: Optional[Decimal] = None
    variance_percentage: Optional[Decimal] = None
    message: Optional[str] = None
    evidence: Optional[dict[str, Any]] = None
    rule_version: str

    class Config:
        from_attributes = True
        populate_by_name = True

class ControlRunSummaryOut(BaseModel):
    run_id: UUID
    invoice_id: UUID
    revision_id: UUID
    run_number: int
    status: str
    total_controls: int
    passed_count: int
    failed_count: int
    warning_count: int
    error_count: int
    not_applicable_count: int
    duration_ms: float
    correlation_id: str

class ControlRunOut(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    invoice_revision_id: UUID
    run_number: int
    status: str
    ruleset_version: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: list[ControlResultOut] = []

    class Config:
        from_attributes = True

class TriggerControlRunRequest(BaseModel):
    revision_id: Optional[UUID] = None
    ruleset_version: str = "v1.0"
