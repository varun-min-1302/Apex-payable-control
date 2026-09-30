from decimal import Decimal
import pytest
from backend.application.services.control_run_service import ControlRunService
from backend.application.dto.decision_dto import DecisionOutcome
from backend.database.models.identity import Tenant
from backend.database.models.ap import (
    Invoice,
    ControlRun,
    ControlResult,
    Exception as APException,
    RiskSignal,
    PayableLedger,
)
from backend.database.models.audit import AuditLog
from backend.database.enums import InvoiceStatus, ControlRunStatus, ControlStatus

@pytest.fixture
def run_service(db_session):
    return ControlRunService(db_session)

@pytest.fixture
def tenant(db_session):
    return db_session.query(Tenant).first()

def test_scenario_a_clean_invoice(run_service, tenant, db_session):
    """
    Scenario A: INV-2026-0001
    Clean invoice matching approved PO and Goods Receipt.
    Expected: Decision PASS, status AWAITING_APPROVAL, 0 exceptions, 0 payables created.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    assert invoice is not None

    initial_payable_count = db_session.query(PayableLedger).count()

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome in (DecisionOutcome.PASS, DecisionOutcome.PASS_WITH_WARNING)
    assert run.status == ControlRunStatus.PASSED.value
    assert invoice.status in (InvoiceStatus.AWAITING_APPROVAL.value, InvoiceStatus.APPROVED.value)
    assert len(decision.pending_exceptions) == 0

    # INVARIANT CHECK: Control Engine never creates a payable!
    assert db_session.query(PayableLedger).count() == initial_payable_count

def test_scenario_b_quantity_mismatch(run_service, tenant, db_session):
    """
    Scenario B: INV-2026-0002
    Invoiced quantity (100) exceeds accepted goods receipt quantity (80).
    Expected: Decision EXCEPTION, status EXCEPTION, exception QUANTITY_MISMATCH.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0002").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome == DecisionOutcome.EXCEPTION
    assert run.status == ControlRunStatus.FAILED.value
    assert invoice.status == InvoiceStatus.EXCEPTION.value

    exc_codes = [e.exception_code for e in decision.pending_exceptions]
    assert "QUANTITY_MISMATCH" in exc_codes

def test_scenario_c_price_mismatch(run_service, tenant, db_session):
    """
    Scenario C: INV-2026-0003
    Invoiced unit price (1850) exceeds approved PO price (1500).
    Expected: Decision EXCEPTION, status EXCEPTION, exception PRICE_MISMATCH.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0003").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome == DecisionOutcome.EXCEPTION
    assert run.status == ControlRunStatus.FAILED.value
    assert invoice.status == InvoiceStatus.EXCEPTION.value

    exc_codes = [e.exception_code for e in decision.pending_exceptions]
    assert "PRICE_MISMATCH" in exc_codes

def test_scenario_d_missing_po(run_service, tenant, db_session):
    """
    Scenario D: INV-2026-0004
    Invoice missing purchase order (purchase_order_id is NULL).
    Expected: Decision EXCEPTION, status EXCEPTION, exception PO_NOT_FOUND.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0004").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome == DecisionOutcome.EXCEPTION
    assert invoice.status == InvoiceStatus.EXCEPTION.value

    exc_codes = [e.exception_code for e in decision.pending_exceptions]
    assert "PO_NOT_FOUND" in exc_codes

def test_scenario_e_vendor_mismatch(run_service, tenant, db_session):
    """
    Scenario E: INV-2026-0005
    Invoice vendor does not match purchase order vendor.
    Expected: Decision EXCEPTION, status EXCEPTION, exception VENDOR_MISMATCH.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0005").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome == DecisionOutcome.EXCEPTION
    assert invoice.status == InvoiceStatus.EXCEPTION.value

    exc_codes = [e.exception_code for e in decision.pending_exceptions]
    assert "VENDOR_MISMATCH" in exc_codes

def test_scenario_f_partial_receipt(run_service, tenant, db_session):
    """
    Scenario F: INV-2026-0006
    PO Qty = 100, Partial GR Qty = 50, Invoiced Qty = 50.
    Invoiced quantity matches accepted partial receipt.
    Expected: Decision PASS, status AWAITING_APPROVAL.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0006").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome in (DecisionOutcome.PASS, DecisionOutcome.PASS_WITH_WARNING)
    assert invoice.status == InvoiceStatus.AWAITING_APPROVAL.value
    assert len(decision.pending_exceptions) == 0

def test_scenario_g_exact_duplicate(run_service, tenant, db_session):
    """
    Scenario G: INV-2026-0007
    Exact duplicate of INV-2026-0001 by document SHA-256 hash.
    Expected: Decision EXCEPTION, status EXCEPTION, exception DUPLICATE_INVOICE.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0007").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome == DecisionOutcome.EXCEPTION
    assert invoice.status == InvoiceStatus.EXCEPTION.value

    exc_codes = [e.exception_code for e in decision.pending_exceptions]
    assert "DUPLICATE_INVOICE" in exc_codes

def test_scenario_h_semantic_duplicate_not_applicable(run_service, tenant, db_session):
    """
    Scenario H: INV-2026-0008
    CRITICAL REQUIREMENT:
    Semantic similarity embeddings are 0 rows in database.
    Must evaluate DUPLICATE_SEMANTIC as NOT_APPLICABLE honestly without fabricating fake AI scores.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0008").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    # Check the specific evaluation for DUPLICATE_SEMANTIC
    sem_res = (
        db_session.query(ControlResult)
        .filter(ControlResult.control_run_id == run.id, ControlResult.control_code == "DUPLICATE_SEMANTIC")
        .first()
    )
    assert sem_res is not None
    assert str(sem_res.status) == "NOT_APPLICABLE"
    assert "vector embeddings have not been generated" in sem_res.message.lower()

def test_scenario_i_tax_mismatch(run_service, tenant, db_session):
    """
    Scenario I: INV-2026-0009
    Invoice claimed tax (15,000) does not match calculated tax (18,000).
    Expected: Decision EXCEPTION, status EXCEPTION, exception TAX_CALCULATION_ERROR.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0009").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome == DecisionOutcome.EXCEPTION
    assert invoice.status == InvoiceStatus.EXCEPTION.value

    exc_codes = [e.exception_code for e in decision.pending_exceptions]
    assert "TAX_CALCULATION_ERROR" in exc_codes

def test_scenario_j_total_mismatch(run_service, tenant, db_session):
    """
    Scenario J: INV-2026-0010
    Invoice claimed grand total (64,000) does not equal subtotal + tax (59,000).
    Expected: Decision EXCEPTION, status EXCEPTION, exception TOTAL_CALCULATION_ERROR.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0010").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome == DecisionOutcome.EXCEPTION
    assert invoice.status == InvoiceStatus.EXCEPTION.value

    exc_codes = [e.exception_code for e in decision.pending_exceptions]
    assert "TOTAL_CALCULATION_ERROR" in exc_codes

def test_scenario_k_bank_mismatch(run_service, tenant, db_session):
    """
    Scenario K: INV-2026-0011
    Invoice bank account hash does not match vendor master bank account hash.
    Expected: Decision EXCEPTION, status EXCEPTION, high-risk exception BANK_DETAILS_MISMATCH.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0011").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome == DecisionOutcome.EXCEPTION
    assert invoice.status == InvoiceStatus.EXCEPTION.value

    exc_codes = [e.exception_code for e in decision.pending_exceptions]
    assert "BANK_DETAILS_MISMATCH" in exc_codes

def test_scenario_l_threshold_proximity(run_service, tenant, db_session):
    """
    Scenario L: INV-2026-0012
    Invoice total ₹99,800 is within buffer of ₹100,000 approval policy threshold.
    Expected: Decision PASS_WITH_WARNING, status AWAITING_APPROVAL, risk signal THRESHOLD_PROXIMITY.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0012").first()
    assert invoice is not None

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    assert decision.outcome == DecisionOutcome.PASS_WITH_WARNING
    assert invoice.status == InvoiceStatus.AWAITING_APPROVAL.value

    sig_codes = [s.signal_code for s in decision.pending_risk_signals]
    assert "THRESHOLD_PROXIMITY" in sig_codes

def test_scenario_m_revision_2_corrected(run_service, tenant, db_session):
    """
    Scenario M: INV-2026-0013
    Invoice has Revision 2 with corrected values.
    Validating Revision 2 passes all controls.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0013").first()
    assert invoice is not None
    assert len(invoice.revisions) == 2
    rev2 = [r for r in invoice.revisions if r.revision_number == 2][0]

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id, revision_id=rev2.id)

    assert decision.outcome in (DecisionOutcome.PASS, DecisionOutcome.PASS_WITH_WARNING)
    assert run.status == ControlRunStatus.PASSED.value

def test_scenario_n_payable_eligibility_without_ledger_creation(run_service, tenant, db_session):
    """
    Scenario N: INV-2026-0014
    CORE PRINCIPLE VERIFICATION:
    Control Engine validates that an invoice is eligible for approval,
    but NEVER inserts a new record into ap.payable_ledger.
    """
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0014").first()
    assert invoice is not None

    initial_payable_count = db_session.query(PayableLedger).count()

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    after_payable_count = db_session.query(PayableLedger).count()
    assert after_payable_count == initial_payable_count, "Control engine created a payable ledger record!"

def test_audit_logs_recorded_for_control_run(run_service, tenant, db_session):
    """Verify that every control run emits structured audit logs into audit.audit_logs."""
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()

    initial_audit_count = db_session.query(AuditLog).count()

    run, summary, decision = run_service.execute_control_run(tenant.id, invoice.id)

    after_audit_count = db_session.query(AuditLog).count()
    assert after_audit_count >= initial_audit_count + 2  # Started + Completed events
