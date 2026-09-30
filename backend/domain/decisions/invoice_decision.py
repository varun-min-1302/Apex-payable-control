from backend.application.dto.control_dto import ControlEvaluation
from backend.application.dto.decision_dto import (
    DecisionOutcome,
    InvoiceDecision,
    PendingException,
    PendingRiskSignal,
)
from backend.database.enums import (
    ControlCode,
    ControlStatus,
    InvoiceStatus,
    SeverityLevel,
)

# Deterministic mapping of failed controls to standard exception codes and titles
EXCEPTION_CODE_MAP: dict[str, tuple[str, str]] = {
    ControlCode.PRICE_MATCH.value: ("PRICE_MISMATCH", "Invoice unit price exceeds approved purchase order price"),
    ControlCode.QUANTITY_MATCH.value: ("QUANTITY_MISMATCH", "Invoiced quantity exceeds accepted goods receipt quantity"),
    ControlCode.RECEIPT_MATCH.value: ("QUANTITY_MISMATCH", "Invoiced quantity exceeds received warehouse quantity"),
    ControlCode.PO_EXISTS.value: ("PO_NOT_FOUND", "Referenced purchase order does not exist in procurement master"),
    ControlCode.PO_APPROVED.value: ("PO_NOT_APPROVED", "Referenced purchase order has not been approved"),
    ControlCode.PO_VENDOR_MATCH.value: ("VENDOR_MISMATCH", "Invoice vendor does not match purchase order vendor"),
    ControlCode.PO_ITEM_MATCH.value: ("PO_ITEM_MISMATCH", "Invoice line items do not correspond to purchase order lines"),
    ControlCode.BANK_DETAILS_MATCH.value: ("BANK_DETAILS_MISMATCH", "Invoice banking details fingerprint does not match approved vendor master"),
    ControlCode.DUPLICATE_EXACT.value: ("DUPLICATE_INVOICE", "Invoice is an exact duplicate of a previously submitted document"),
    ControlCode.TAX_VALIDATION.value: ("TAX_CALCULATION_ERROR", "Invoice tax calculation does not match mathematical statutory rate"),
    ControlCode.TOTAL_VALIDATION.value: ("TOTAL_CALCULATION_ERROR", "Invoice claimed total does not equal sum of parts"),
    ControlCode.VENDOR_STATUS.value: ("VENDOR_INACTIVE", "Vendor is in an inactive, blocked, or pending status"),
    ControlCode.VENDOR_EXISTS.value: ("VENDOR_NOT_FOUND", "Invoice vendor does not exist in master records"),
    ControlCode.VENDOR_TAX_ID_MATCH.value: ("TAX_ID_MISMATCH", "Invoice tax identification number does not match vendor master"),
}

class InvoiceDecisionEngine:
    """
    Renders an explainable decision on an invoice revision based on all control evaluations.
    Maps control failures to pending exceptions and warnings to risk signals.
    """

    def evaluate(self, evaluations: list[ControlEvaluation]) -> InvoiceDecision:
        failed_evals = [e for e in evaluations if e.status == ControlStatus.FAIL]
        warning_evals = [e for e in evaluations if e.status == ControlStatus.WARNING]
        error_evals = [e for e in evaluations if e.status == ControlStatus.ERROR]

        pending_exceptions: list[PendingException] = []
        pending_risk_signals: list[PendingRiskSignal] = []

        # 1. Map failures to pending exceptions
        for ev in failed_evals:
            code_and_title = EXCEPTION_CODE_MAP.get(
                ev.control_code,
                (f"{ev.control_code}_EXCEPTION", f"Control {ev.control_code} validation failure")
            )
            exc_code, title = code_and_title
            pending_exceptions.append(
                PendingException(
                    exception_code=exc_code,
                    title=title,
                    description=ev.message,
                    severity=ev.severity.value if hasattr(ev.severity, "value") else str(ev.severity),
                    control_code=ev.control_code,
                    evidence=ev.evidence or {"actual": ev.actual_value, "expected": ev.expected_value}
                )
            )

        # 2. Map warnings to pending risk signals
        for ev in warning_evals:
            pending_risk_signals.append(
                PendingRiskSignal(
                    signal_code=ev.control_code,
                    category=ev.category,
                    severity=ev.severity.value if hasattr(ev.severity, "value") else str(ev.severity),
                    description=ev.message,
                    evidence=ev.evidence or {"actual": ev.actual_value}
                )
            )

        # 3. Determine decision outcome and target invoice status
        if error_evals:
            outcome = DecisionOutcome.ERROR
            target_status = InvoiceStatus.VALIDATING
            summary = f"Control run encountered {len(error_evals)} technical evaluation error(s)."
        elif failed_evals:
            outcome = DecisionOutcome.EXCEPTION
            target_status = InvoiceStatus.EXCEPTION
            failed_codes = ", ".join([e.control_code for e in failed_evals])
            summary = f"Invoice failed {len(failed_evals)} control check(s): {failed_codes}."
        elif warning_evals:
            outcome = DecisionOutcome.PASS_WITH_WARNING
            target_status = InvoiceStatus.AWAITING_APPROVAL
            warning_codes = ", ".join([e.control_code for e in warning_evals])
            summary = f"All controls passed with {len(warning_evals)} risk warning(s): {warning_codes}. Eligible for approval."
        else:
            outcome = DecisionOutcome.PASS
            target_status = InvoiceStatus.AWAITING_APPROVAL
            summary = "All controls passed successfully. Invoice is verified and eligible for approval."

        return InvoiceDecision(
            outcome=outcome,
            target_invoice_status=target_status,
            summary_message=summary,
            failed_evaluations=failed_evals,
            warning_evaluations=warning_evals,
            pending_exceptions=pending_exceptions,
            pending_risk_signals=pending_risk_signals,
        )
