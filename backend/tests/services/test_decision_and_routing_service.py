import uuid
from decimal import Decimal
import pytest
from backend.domain.decisions.invoice_decision import InvoiceDecisionEngine
from backend.application.services.approval_routing_service import ApprovalRoutingService
from backend.repositories.approval_repository import ApprovalRepository
from backend.application.dto.control_dto import ControlEvaluation
from backend.application.dto.decision_dto import DecisionOutcome
from backend.database.models.identity import Tenant
from backend.database.models.ap import Invoice, InvoiceRevision, ApprovalPolicy, PayableLedger
from backend.database.enums import ControlStatus, SeverityLevel, InvoiceStatus

def test_decision_engine_all_pass():
    engine = InvoiceDecisionEngine()
    evals = [
        ControlEvaluation(control_code="VENDOR_EXISTS", category="VENDOR", status=ControlStatus.PASS, severity=SeverityLevel.INFO, message="ok"),
        ControlEvaluation(control_code="PRICE_MATCH", category="FINANCIAL", status=ControlStatus.PASS, severity=SeverityLevel.INFO, message="ok"),
    ]
    dec = engine.evaluate(evals)
    assert dec.outcome == DecisionOutcome.PASS
    assert dec.target_invoice_status == InvoiceStatus.AWAITING_APPROVAL
    assert len(dec.pending_exceptions) == 0

def test_decision_engine_with_warning():
    engine = InvoiceDecisionEngine()
    evals = [
        ControlEvaluation(control_code="VENDOR_EXISTS", category="VENDOR", status=ControlStatus.PASS, severity=SeverityLevel.INFO, message="ok"),
        ControlEvaluation(control_code="THRESHOLD_PROXIMITY", category="APPROVAL", status=ControlStatus.WARNING, severity=SeverityLevel.MEDIUM, message="close to threshold"),
    ]
    dec = engine.evaluate(evals)
    assert dec.outcome == DecisionOutcome.PASS_WITH_WARNING
    assert dec.target_invoice_status == InvoiceStatus.AWAITING_APPROVAL
    assert len(dec.pending_risk_signals) == 1
    assert dec.pending_risk_signals[0].signal_code == "THRESHOLD_PROXIMITY"

def test_decision_engine_with_failure():
    engine = InvoiceDecisionEngine()
    evals = [
        ControlEvaluation(control_code="PRICE_MATCH", category="FINANCIAL", status=ControlStatus.FAIL, severity=SeverityLevel.HIGH, message="Price mismatch"),
    ]
    dec = engine.evaluate(evals)
    assert dec.outcome == DecisionOutcome.EXCEPTION
    assert dec.target_invoice_status == InvoiceStatus.EXCEPTION
    assert len(dec.pending_exceptions) == 1
    assert dec.pending_exceptions[0].exception_code == "PRICE_MISMATCH"

def test_approval_routing_blocks_on_failing_controls(db_session):
    tenant = db_session.query(Tenant).first()
    invoice = db_session.query(Invoice).first()

    routing_svc = ApprovalRoutingService(ApprovalRepository(db_session))
    # controls failed
    plan = routing_svc.determine_routing(tenant.id, invoice, is_controls_passed=False)
    assert plan.is_eligible_for_approval is False
    assert len(plan.steps) == 0
    assert "failed mandatory control checks" in plan.reason

def test_approval_routing_succeeds_on_passed_controls(db_session):
    tenant = db_session.query(Tenant).first()
    invoice = db_session.query(Invoice).first()

    routing_svc = ApprovalRoutingService(ApprovalRepository(db_session))
    plan = routing_svc.determine_routing(tenant.id, invoice, is_controls_passed=True)
    assert plan.is_eligible_for_approval is True
    assert len(plan.steps) > 0

def test_approval_routing_never_creates_payable_ledger(db_session):
    """
    CORE INVARIANT VERIFICATION:
    The approval routing service must never insert a row into ap.payable_ledger.
    """
    tenant = db_session.query(Tenant).first()
    invoice = db_session.query(Invoice).first()

    initial_payable_count = db_session.query(PayableLedger).count()

    routing_svc = ApprovalRoutingService(ApprovalRepository(db_session))
    created_approvals = routing_svc.route_approvals(tenant.id, invoice, is_controls_passed=True)

    after_payable_count = db_session.query(PayableLedger).count()
    assert after_payable_count == initial_payable_count, "Payable was erroneously created by approval routing!"
    db_session.rollback()
