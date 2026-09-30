from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class ApprovalRouteStep:
    """A required approval checkpoint derived from policy."""
    policy_id: UUID
    policy_name: str
    sequence_order: int
    required_role: str
    min_amount: Decimal
    max_amount: Optional[Decimal]
    requires_all_controls_pass: bool

@dataclass(frozen=True)
class ApprovalRoutingPlan:
    """Approval route computed for an invoice."""
    invoice_id: UUID
    is_eligible_for_approval: bool
    requires_all_controls_pass: bool
    steps: list[ApprovalRouteStep] = field(default_factory=list)
    reason: str = ""
