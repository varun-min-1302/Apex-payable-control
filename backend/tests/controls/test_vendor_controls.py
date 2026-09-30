import uuid
from decimal import Decimal
import pytest
from backend.domain.controls.vendor_controls import (
    VendorExistsControl,
    VendorStatusControl,
    VendorTaxIdMatchControl,
    BankDetailsMatchControl,
)
from backend.domain.controls.base import ControlContext
from backend.database.models.identity import Tenant
from backend.database.models.procurement import Vendor
from backend.database.models.ap import Invoice, InvoiceRevision
from backend.database.enums import ControlStatus, SeverityLevel, VendorStatus

@pytest.fixture
def base_context(db_session):
    tenant = db_session.query(Tenant).first()
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    vendor = db_session.query(Vendor).filter(Vendor.id == invoice.vendor_id).first()
    revision = invoice.revisions[0]
    return ControlContext(
        tenant_id=tenant.id,
        invoice=invoice,
        current_revision=revision,
        invoice_items=list(revision.items),
        vendor=vendor,
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )

def test_vendor_exists_control_pass(base_context):
    ctrl = VendorExistsControl()
    res = ctrl.execute(base_context)
    assert res.status == ControlStatus.PASS
    assert res.severity == SeverityLevel.INFO

def test_vendor_exists_control_fail(base_context):
    # Context with missing vendor
    ctx = ControlContext(
        tenant_id=base_context.tenant_id,
        invoice=base_context.invoice,
        current_revision=base_context.current_revision,
        invoice_items=base_context.invoice_items,
        vendor=None, # Missing vendor
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = VendorExistsControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.CRITICAL

def test_vendor_status_control_pass(base_context):
    ctrl = VendorStatusControl()
    res = ctrl.execute(base_context)
    assert res.status == ControlStatus.PASS

def test_vendor_status_control_inactive_fail(base_context):
    # Mock vendor with BLOCKED status
    vendor_blocked = Vendor(
        id=base_context.vendor.id,
        tenant_id=base_context.tenant_id,
        vendor_code="BLOCKED-V",
        legal_name="Blocked Vendor",
        display_name="Blocked Vendor",
        tax_identifier="27AA123",
        status=VendorStatus.BLOCKED.value
    )
    ctx = ControlContext(
        tenant_id=base_context.tenant_id,
        invoice=base_context.invoice,
        current_revision=base_context.current_revision,
        invoice_items=base_context.invoice_items,
        vendor=vendor_blocked,
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = VendorStatusControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH

def test_vendor_tax_id_match_control_pass(base_context):
    ctrl = VendorTaxIdMatchControl()
    res = ctrl.execute(base_context)
    assert res.status == ControlStatus.PASS

def test_vendor_tax_id_match_control_mismatch(base_context):
    # Revision with different tax ID
    rev_mismatch = InvoiceRevision(
        id=base_context.current_revision.id,
        tenant_id=base_context.tenant_id,
        invoice_id=base_context.invoice.id,
        revision_number=1,
        invoice_number="INV-1",
        vendor_tax_id_as_submitted="INVALID_TAX_ID_999",
        subtotal=Decimal("100.00"),
        grand_total=Decimal("118.00")
    )
    ctx = ControlContext(
        tenant_id=base_context.tenant_id,
        invoice=base_context.invoice,
        current_revision=rev_mismatch,
        invoice_items=base_context.invoice_items,
        vendor=base_context.vendor,
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = VendorTaxIdMatchControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH

def test_bank_details_match_control_pass(base_context):
    ctrl = BankDetailsMatchControl()
    res = ctrl.execute(base_context)
    assert res.status == ControlStatus.PASS

def test_bank_details_match_control_fraud_mismatch(base_context):
    # Revision with fraud bank hash
    rev_fraud = InvoiceRevision(
        id=base_context.current_revision.id,
        tenant_id=base_context.tenant_id,
        invoice_id=base_context.invoice.id,
        revision_number=1,
        invoice_number="INV-1",
        bank_account_hash="0000000000000000000000000000000000000000000000000000000000000000",
        bank_account_last4="9999",
        subtotal=Decimal("100.00"),
        grand_total=Decimal("118.00")
    )
    ctx = ControlContext(
        tenant_id=base_context.tenant_id,
        invoice=base_context.invoice,
        current_revision=rev_fraud,
        invoice_items=base_context.invoice_items,
        vendor=base_context.vendor,
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = BankDetailsMatchControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.CRITICAL
    assert "rerouting fraud" in res.message.lower()
