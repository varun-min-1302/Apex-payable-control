from decimal import Decimal
import pytest
from sqlalchemy import text
from backend.database.models.identity import Tenant, User, Role
from backend.database.models.procurement import Vendor, PurchaseOrder, GoodsReceipt
from backend.database.models.ap import (
    Invoice, InvoiceRevision, ControlRun, ControlResult,
    RiskSignal, Exception, ApprovalPolicy, Approval,
    PayableLedger, Payment
)
from backend.database.models.audit import AuditLog
from backend.database.enums import InvoiceStatus, PayableStatus

def test_seed_record_counts(db_session):
    """Verify that the seeded database contains all expected entity counts."""
    assert db_session.query(Tenant).count() >= 1
    assert db_session.query(Role).count() == 7
    assert db_session.query(User).count() == 9
    assert db_session.query(Vendor).count() == 10
    assert db_session.query(PurchaseOrder).count() == 30
    assert db_session.query(GoodsReceipt).count() == 30
    assert db_session.query(Invoice).count() >= 40
    assert db_session.query(InvoiceRevision).count() >= 41
    assert db_session.query(ControlRun).count() >= 40
    assert db_session.query(ControlResult).count() >= 400
    assert db_session.query(RiskSignal).count() >= 4
    assert db_session.query(Exception).count() >= 5
    assert db_session.query(ApprovalPolicy).count() >= 4
    assert db_session.query(Approval).count() >= 14
    assert db_session.query(PayableLedger).count() >= 11
    assert db_session.query(Payment).count() >= 6
    assert db_session.query(AuditLog).count() >= 100

def test_core_principle_received_is_not_payable(db_session):
    """
    Core Principle: RECEIVED INVOICE != PAYABLE OBLIGATION
    Ensure no invoice in EXCEPTION, REJECTED, or RECEIVED status exists in payable_ledger.
    """
    invalid_payables = (
        db_session.query(PayableLedger)
        .join(Invoice, PayableLedger.invoice_id == Invoice.id)
        .filter(Invoice.status.in_([InvoiceStatus.EXCEPTION, InvoiceStatus.REJECTED, InvoiceStatus.RECEIVED]))
        .count()
    )
    assert invalid_payables == 0, "Disallowed invoices found in payable_ledger!"

def test_financial_types_are_decimal(db_session):
    """Verify all monetary values are Decimal (never float)."""
    invoice = db_session.query(InvoiceRevision).first()
    assert isinstance(invoice.subtotal, Decimal)
    assert isinstance(invoice.tax_total, Decimal)
    assert isinstance(invoice.grand_total, Decimal)

    po = db_session.query(PurchaseOrder).first()
    assert isinstance(po.subtotal, Decimal)
    assert isinstance(po.tax_total, Decimal)
    assert isinstance(po.grand_total, Decimal)

def test_scenarios_a_through_o_conformance(db_session):
    """Verify all 15 deliberate scenarios from the prompt exist with correct status."""
    # Scenario A: Clean 3-way match, APPROVED, has positive approval
    inv_a = db_session.query(Invoice).filter(Invoice.invoice_number == 'INV-2026-0001').first()
    assert inv_a is not None
    assert str(inv_a.status) == 'APPROVED'
    appr_a = db_session.query(Approval).filter(Approval.invoice_id == inv_a.id).first()
    assert appr_a is not None
    assert appr_a.decision == 'APPROVE'

    # Scenario B: Quantity mismatch
    exc_b = db_session.query(Exception).join(Invoice).filter(Invoice.invoice_number == 'INV-2026-0002').first()
    assert exc_b is not None
    assert exc_b.exception_code == 'QUANTITY_MISMATCH'

    # Scenario C: Price mismatch
    exc_c = db_session.query(Exception).join(Invoice).filter(Invoice.invoice_number == 'INV-2026-0003').first()
    assert exc_c is not None
    assert exc_c.exception_code == 'PRICE_MISMATCH'

    # Scenario D: PO missing
    exc_d = db_session.query(Exception).join(Invoice).filter(Invoice.invoice_number == 'INV-2026-0004').first()
    assert exc_d is not None
    assert exc_d.exception_code == 'PO_NOT_FOUND'

    # Scenario E: Vendor mismatch
    cr_e = (
        db_session.query(ControlResult)
        .join(Invoice)
        .filter(Invoice.invoice_number == 'INV-2026-0005', ControlResult.control_code == 'PO_VENDOR_MATCH')
        .first()
    )
    assert cr_e is not None
    assert str(cr_e.status) == 'FAIL'

    # Scenario F: Partial receipt
    inv_f = db_session.query(Invoice).filter(Invoice.invoice_number == 'INV-2026-0006').first()
    assert inv_f is not None
    assert str(inv_f.status) == 'AWAITING_APPROVAL'

    # Scenario G: Exact duplicate
    exc_g = db_session.query(Exception).join(Invoice).filter(Invoice.invoice_number == 'INV-2026-0007').first()
    assert exc_g is not None
    assert exc_g.exception_code == 'DUPLICATE_INVOICE'

    # Scenario H: Semantic duplicate
    sig_h = db_session.query(RiskSignal).join(Invoice).filter(Invoice.invoice_number == 'INV-2026-0008').first()
    assert sig_h is not None
    assert sig_h.signal_code == 'SEMANTIC_SIMILARITY'

    # Scenario I: Tax calculation error
    cr_i = (
        db_session.query(ControlResult)
        .join(Invoice)
        .filter(Invoice.invoice_number == 'INV-2026-0009', ControlResult.control_code == 'TAX_VALIDATION')
        .first()
    )
    assert cr_i is not None
    assert str(cr_i.status) == 'FAIL'

    # Scenario J: Total math error
    cr_j = (
        db_session.query(ControlResult)
        .join(Invoice)
        .filter(Invoice.invoice_number == 'INV-2026-0010', ControlResult.control_code == 'TOTAL_VALIDATION')
        .first()
    )
    assert cr_j is not None
    assert str(cr_j.status) == 'FAIL'

    # Scenario K: Bank details mismatch / fraud hold
    exc_k = db_session.query(Exception).join(Invoice).filter(Invoice.invoice_number == 'INV-2026-0011').first()
    assert exc_k is not None
    assert exc_k.exception_code == 'BANK_DETAILS_MISMATCH'

    # Scenario L: Threshold proximity (99,800 vs 100,000 threshold)
    sig_l = db_session.query(RiskSignal).join(Invoice).filter(Invoice.invoice_number == 'INV-2026-0012').first()
    assert sig_l is not None
    assert sig_l.signal_code == 'THRESHOLD_PROXIMITY'

    # Scenario M: Corrected Revision 2
    inv_m = db_session.query(Invoice).filter(Invoice.invoice_number == 'INV-2026-0013').first()
    assert inv_m is not None
    assert len(inv_m.revisions) == 2

    # Scenario N: Payable created and partially paid
    inv_n = db_session.query(Invoice).filter(Invoice.invoice_number == 'INV-2026-0014').first()
    assert inv_n is not None
    payable_n = db_session.query(PayableLedger).filter(PayableLedger.invoice_id == inv_n.id).first()
    assert payable_n is not None
    assert str(payable_n.status) == 'PARTIALLY_PAID'
    assert len(payable_n.payments) == 1

    # Scenario O: Rejected invoice
    inv_o = db_session.query(Invoice).filter(Invoice.invoice_number == 'INV-2026-0015').first()
    assert inv_o is not None
    assert str(inv_o.status) == 'REJECTED'
