"""Pydantic schemas for Phase 6 Control Intelligence and Explainability."""
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# 1. Why Isn't This Payable? Schemas
# -----------------------------------------------------------------------------

class BlockingReasonOut(BaseModel):
    control_code: str
    title: str
    what_happened: str
    why_it_matters: str
    recommended_action: str
    severity: str
    expected: str
    actual: str
    variance: str
    technical_rule: str


class InvoiceExplanationOut(BaseModel):
    invoice_id: UUID
    invoice_number: str
    status: str
    headline: str
    summary: str
    blocking_reasons: List[BlockingReasonOut]
    passed_checks: int
    next_action: str
    can_be_paid: bool


# -----------------------------------------------------------------------------
# 2. Control Graph Schemas
# -----------------------------------------------------------------------------

class ControlGraphCheckOut(BaseModel):
    control_code: str
    title: str
    status: str
    severity: str
    message: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    variance: Optional[str] = None
    why_it_matters: Optional[str] = None
    recommended_action: Optional[str] = None
    evaluated_at: Optional[str] = None


class ControlGraphNodeOut(BaseModel):
    id: str
    label: str
    category: str
    order: int
    status: str
    total_checks: int
    passed_count: int
    failed_count: int
    warning_count: int
    summary: str
    checks: List[ControlGraphCheckOut]


class ControlGraphOut(BaseModel):
    invoice_id: UUID
    invoice_number: str
    current_status: str
    nodes: List[ControlGraphNodeOut]


# -----------------------------------------------------------------------------
# 3. Audit Replay Schemas
# -----------------------------------------------------------------------------

class AuditReplayEventOut(BaseModel):
    id: str
    timestamp: str
    actor_name: str
    actor_email: Optional[str] = None
    actor_role: str
    action: str
    title: str
    description: str
    category: str
    entity_type: str
    entity_id: str
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    technical_details: Dict[str, Any] = Field(default_factory=dict)


class AuditReplayOut(BaseModel):
    invoice_id: UUID
    invoice_number: str
    events_count: int
    timeline: List[AuditReplayEventOut]


# -----------------------------------------------------------------------------
# 4. Revision Diff ("What Changed?") Schemas
# -----------------------------------------------------------------------------

class HeaderDiffOut(BaseModel):
    field: str
    label: str
    previous_value: str
    new_value: str


class LineItemDiffOut(BaseModel):
    line_number: int
    change_type: str
    description: str
    changes: Optional[List[str]] = None
    previous: str
    current: str


class RevisionComparisonOut(BaseModel):
    from_revision_number: int
    to_revision_number: int
    changed_by: str
    changed_by_email: Optional[str] = None
    changed_at: str
    header_diffs: List[HeaderDiffOut]
    item_diffs: List[LineItemDiffOut]
    controls_rerun: bool
    resulting_control_status: str


class RevisionDiffOut(BaseModel):
    invoice_id: UUID
    invoice_number: str
    has_multiple_revisions: bool
    revisions_count: int
    diffs: List[RevisionComparisonOut]


# -----------------------------------------------------------------------------
# 5. Dashboard Control Health Schemas
# -----------------------------------------------------------------------------

class ControlCategoryHealthOut(BaseModel):
    category: str
    name: str
    total_checks: int
    passed_count: int
    failed_count: int
    warning_count: int
    pass_rate_percentage: float


class StatusBreakdownOut(BaseModel):
    received: int
    processing: int
    needs_attention: int
    waiting_for_approval: int
    approved: int
    payable: int
    paid: int
    rejected: int


class TopRecurringIssueOut(BaseModel):
    control_code: str
    title: str
    failure_count: int
    why_it_matters: str


class DashboardControlHealthOut(BaseModel):
    overall_pass_rate_percentage: float
    total_checks_evaluated: int
    categories: List[ControlCategoryHealthOut]
    status_breakdown: StatusBreakdownOut
    top_recurring_issues: List[TopRecurringIssueOut]
