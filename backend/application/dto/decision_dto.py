from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import UUID
from backend.database.enums import InvoiceStatus
from backend.application.dto.control_dto import ControlEvaluation

class DecisionOutcome(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNING = "PASS_WITH_WARNING"
    EXCEPTION = "EXCEPTION"
    ERROR = "ERROR"

@dataclass(frozen=True)
class PendingException:
    """An exception determined by a failing control."""
    exception_code: str
    title: str
    description: str
    severity: str
    control_code: str
    evidence: Optional[dict[str, Any]] = None

@dataclass(frozen=True)
class PendingRiskSignal:
    """A risk signal determined by a warning or anomaly control."""
    signal_code: str
    category: str
    severity: str
    description: str
    score: Optional[float] = None
    confidence: Optional[float] = None
    evidence: Optional[dict[str, Any]] = None

@dataclass(frozen=True)
class InvoiceDecision:
    """
    Final decision rendered by the Decision Engine on an invoice revision.
    Determines next state, exceptions to create, and risk signals to generate.
    """
    outcome: DecisionOutcome
    target_invoice_status: InvoiceStatus
    summary_message: str
    failed_evaluations: list[ControlEvaluation] = field(default_factory=list)
    warning_evaluations: list[ControlEvaluation] = field(default_factory=list)
    pending_exceptions: list[PendingException] = field(default_factory=list)
    pending_risk_signals: list[PendingRiskSignal] = field(default_factory=list)
