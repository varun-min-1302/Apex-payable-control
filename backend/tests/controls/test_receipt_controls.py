import uuid
from decimal import Decimal
import pytest
from backend.domain.controls.receipt_controls import ReceiptMatchControl, QuantityMatchControl
from backend.domain.controls.base import ControlContext
from backend.application.dto.control_dto import ToleranceConfig
from backend.database.models.identity import Tenant
from backend.database.models.procurement import Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem
from backend.database.models.ap import Invoice, InvoiceRevision, InvoiceItem
from backend.database.enums import ControlStatus, SeverityLevel

@pytest.fixture
def receipt_context(db_session):
    tenant = db_session.query(Tenant).first()
    vendor = db_session.query(Vendor).first()
    po = db_session.query(PurchaseOrder).first()
    grs = list(po.goods_receipts)
    gr_items = [item for gr in grs for item in gr.items]
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
        goods_receipts=grs,
        goods_receipt_items=gr_items,
        approval_policies=[],
        tolerance_config=ToleranceConfig()
    )

def test_receipt_match_control_pass(receipt_context):
    ctrl = ReceiptMatchControl()
    res = ctrl.execute(receipt_context)
    assert res.status == ControlStatus.PASS
    assert res.severity == SeverityLevel.INFO

def test_receipt_match_control_no_receipts_fail(receipt_context):
    ctx = ControlContext(
        tenant_id=receipt_context.tenant_id,
        invoice=receipt_context.invoice,
        current_revision=receipt_context.current_revision,
        invoice_items=receipt_context.invoice_items,
        vendor=receipt_context.vendor,
        purchase_order=receipt_context.purchase_order,
        po_items=receipt_context.po_items,
        goods_receipts=[], # Zero goods receipts
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = ReceiptMatchControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH
    assert "No goods receipts found" in res.message

def test_receipt_match_control_over_invoiced_fail(receipt_context):
    # Invoice item with huge quantity exceeding GR
    over_item = InvoiceItem(
        id=uuid.uuid4(),
        tenant_id=receipt_context.tenant_id,
        invoice_revision_id=receipt_context.current_revision.id,
        line_number=1,
        product_code=receipt_context.po_items[0].product_code,
        description=receipt_context.po_items[0].description,
        quantity=Decimal("99999.0000"), # Massive quantity!
        unit_price=Decimal("100.00"),
        line_total=Decimal("9999900.00")
    )
    ctx = ControlContext(
        tenant_id=receipt_context.tenant_id,
        invoice=receipt_context.invoice,
        current_revision=receipt_context.current_revision,
        invoice_items=[over_item],
        vendor=receipt_context.vendor,
        purchase_order=receipt_context.purchase_order,
        po_items=receipt_context.po_items,
        goods_receipts=receipt_context.goods_receipts,
        goods_receipt_items=receipt_context.goods_receipt_items,
        approval_policies=[]
    )
    ctrl = ReceiptMatchControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH
    assert res.variance_value > 0

def test_quantity_match_control_pass(receipt_context):
    ctrl = QuantityMatchControl()
    res = ctrl.execute(receipt_context)
    assert res.status == ControlStatus.PASS

def test_quantity_match_control_variance_fail(receipt_context):
    po_item = receipt_context.po_items[0]
    # Invoiced qty: 100, Accepted qty: 80
    inv_item = InvoiceItem(
        id=uuid.uuid4(),
        tenant_id=receipt_context.tenant_id,
        invoice_revision_id=receipt_context.current_revision.id,
        line_number=1,
        product_code=po_item.product_code,
        description=po_item.description,
        quantity=Decimal("100.0000"),
        unit_price=Decimal("50.00"),
        line_total=Decimal("5000.00")
    )
    gr_item = GoodsReceiptItem(
        id=uuid.uuid4(),
        tenant_id=receipt_context.tenant_id,
        goods_receipt_id=uuid.uuid4(),
        purchase_order_item_id=po_item.id,
        received_quantity=Decimal("80.0000"),
        accepted_quantity=Decimal("80.0000"),
        rejected_quantity=Decimal("0.0000")
    )
    ctx = ControlContext(
        tenant_id=receipt_context.tenant_id,
        invoice=receipt_context.invoice,
        current_revision=receipt_context.current_revision,
        invoice_items=[inv_item],
        vendor=receipt_context.vendor,
        purchase_order=receipt_context.purchase_order,
        po_items=[po_item],
        goods_receipts=receipt_context.goods_receipts,
        goods_receipt_items=[gr_item],
        approval_policies=[],
        tolerance_config=ToleranceConfig(quantity_variance_percentage_tolerance=Decimal("0.0000"))
    )
    ctrl = QuantityMatchControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH
    assert res.variance_value == Decimal("20.00")
    assert res.variance_percentage == Decimal("25.0000") # 20 / 80 = 25%
