from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID
from backend.database.enums import ControlCategory, ControlCode, ControlStatus, SeverityLevel

@dataclass(frozen=True)
class ToleranceConfig:
    """Configurable tolerances for deterministic controls."""
    # Absolute & percentage tolerances
    quantity_variance_percentage_tolerance: Decimal = Decimal("0.0000")  # Strict 0% default
    price_variance_percentage_tolerance: Decimal = Decimal("0.0000")     # Strict 0% default
    tax_rounding_tolerance_amount: Decimal = Decimal("0.05")             # ₹0.05 rounding difference allowed
    total_rounding_tolerance_amount: Decimal = Decimal("0.05")           # ₹0.05 rounding difference allowed
    # Proximity buffer for approval thresholds (percentage or fixed amount)
    threshold_proximity_percentage: Decimal = Decimal("2.00")            # within 2% of threshold is flagged
    threshold_proximity_absolute_amount: Decimal = Decimal("5000.00")    # or within ₹5,000

@dataclass(frozen=True)
class ControlEvaluation:
    """
    Structured outcome of an individual control execution.
    Contains complete explainability data: expected vs actual values, variances, and evidence.
    """
    control_code: str
    category: str
    status: ControlStatus
    severity: SeverityLevel
    message: str
    expected_value: Optional[dict[str, Any]] = None
    actual_value: Optional[dict[str, Any]] = None
    variance_value: Optional[Decimal] = None
    variance_percentage: Optional[Decimal] = None
    evidence: Optional[dict[str, Any]] = None
    rule_version: str = "v1.0"

    @property
    def is_failed(self) -> bool:
        return self.status == ControlStatus.FAIL

    @property
    def is_warning(self) -> bool:
        return self.status == ControlStatus.WARNING

    @property
    def is_error(self) -> bool:
        return self.status == ControlStatus.ERROR

    @property
    def is_passed(self) -> bool:
        return self.status == ControlStatus.PASS

@dataclass(frozen=True)
class ControlRunSummary:
    """Summary metrics of a control run."""
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
