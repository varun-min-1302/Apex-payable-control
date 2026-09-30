import uuid
from decimal import Decimal
import pytest
from backend.domain.controls.po_controls import (
    POExistsControl,
    POApprovedControl,
    POVendorMatchControl,
    POItemMatchControl,
)
from backend.domain.controls.base import ControlContext
from backend.database.models.identity import Tenant
from backend.database.models.procurement import Vendor, PurchaseOrder, PurchaseOrderItem
from backend.database.models.ap import Invoice, InvoiceRevision, InvoiceItem
from backend.database.enums import ControlStatus, SeverityLevel, ApprovalStatus, POStatus

@pytest.fixture
def po_context(db_session):
    tenant = db_session.query(Tenant).first()
    vendor = db_session.query(Vendor).first()
    po = db_session.query(PurchaseOrder).filter(PurchaseOrder.vendor_id == vendor.id).first()
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    if not invoice:
        invoice = db_session.query(Invoice).filter(Invoice.purchase_order_id == po.id).first()
    revision = invoice.revisions[0]
    return ControlContext(
        tenant_id=tenant.id,
        invoice=invoice,
        current_revision=revision,
        invoice_items=list(revision.items),
        vendor=vendor,
        purchase_order=po,
        po_items=list(po.items),
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )

def test_po_exists_control_pass(po_context):
    ctrl = POExistsControl()
    res = ctrl.execute(po_context)
    assert res.status == ControlStatus.PASS
    assert res.severity == SeverityLevel.INFO

def test_po_exists_control_missing_fail(po_context):
    ctx = ControlContext(
        tenant_id=po_context.tenant_id,
        invoice=po_context.invoice,
        current_revision=po_context.current_revision,
        invoice_items=po_context.invoice_items,
        vendor=po_context.vendor,
        purchase_order=None, # Missing PO
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = POExistsControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH

def test_po_approved_control_pass(po_context):
    ctrl = POApprovedControl()
    res = ctrl.execute(po_context)
    assert res.status == ControlStatus.PASS

def test_po_approved_control_unapproved_fail(po_context):
    unapproved_po = PurchaseOrder(
        id=po_context.purchase_order.id,
        tenant_id=po_context.tenant_id,
        vendor_id=po_context.vendor.id,
        po_number="PO-DRAFT-1",
        status=POStatus.DRAFT.value,
        approval_status=ApprovalStatus.PENDING.value
    )
    ctx = ControlContext(
        tenant_id=po_context.tenant_id,
        invoice=po_context.invoice,
        current_revision=po_context.current_revision,
        invoice_items=po_context.invoice_items,
        vendor=po_context.vendor,
        purchase_order=unapproved_po,
        po_items=po_context.po_items,
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = POApprovedControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH

def test_po_vendor_match_control_pass(po_context):
    ctrl = POVendorMatchControl()
    res = ctrl.execute(po_context)
    assert res.status == ControlStatus.PASS

def test_po_vendor_match_control_cross_vendor_fail(po_context):
    # PO has different vendor than invoice
    other_vendor_id = uuid.uuid4()
    diff_po = PurchaseOrder(
        id=po_context.purchase_order.id,
        tenant_id=po_context.tenant_id,
        vendor_id=other_vendor_id, # Different vendor!
        po_number="PO-OTHER-V",
        status=POStatus.APPROVED.value,
        approval_status=ApprovalStatus.APPROVED.value
    )
    ctx = ControlContext(
        tenant_id=po_context.tenant_id,
        invoice=po_context.invoice,
        current_revision=po_context.current_revision,
        invoice_items=po_context.invoice_items,
        vendor=po_context.vendor,
        purchase_order=diff_po,
        po_items=po_context.po_items,
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = POVendorMatchControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.CRITICAL

def test_po_item_match_control_pass(po_context):
    ctrl = POItemMatchControl()
    res = ctrl.execute(po_context)
    assert res.status == ControlStatus.PASS

def test_po_item_match_control_unmatched_item_fail(po_context):
    # Invoice item with random product code not in PO
    unmatched_item = InvoiceItem(
        id=uuid.uuid4(),
        tenant_id=po_context.tenant_id,
        invoice_revision_id=po_context.current_revision.id,
        line_number=99,
        product_code="UNMATCHED-SKU-999",
        description="Unrelated Item Completely",
        quantity=Decimal("1.0000"),
        unit_price=Decimal("100.00"),
        line_total=Decimal("100.00")
    )
    ctx = ControlContext(
        tenant_id=po_context.tenant_id,
        invoice=po_context.invoice,
        current_revision=po_context.current_revision,
        invoice_items=[unmatched_item],
        vendor=po_context.vendor,
        purchase_order=po_context.purchase_order,
        po_items=po_context.po_items,
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = POItemMatchControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH
    assert "could not be matched" in res.message
