from datetime import date, timedelta
from decimal import Decimal
import pytest
from backend.domain.controls.financial_controls import (
    PriceMatchControl,
    TaxValidationControl,
    TotalValidationControl,
    PaymentTermsControl,
)
from backend.domain.controls.base import ControlContext
from backend.application.dto.control_dto import ToleranceConfig
from backend.database.models.identity import Tenant
from backend.database.models.procurement import Vendor, PurchaseOrder, PurchaseOrderItem
from backend.database.models.ap import Invoice, InvoiceRevision, InvoiceItem
from backend.database.enums import ControlStatus, SeverityLevel

@pytest.fixture
def financial_context(db_session):
    tenant = db_session.query(Tenant).first()
    vendor = db_session.query(Vendor).first()
    po = db_session.query(PurchaseOrder).first()
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
        approval_policies=[],
        tolerance_config=ToleranceConfig()
    )

def test_price_match_control_pass(financial_context):
    ctrl = PriceMatchControl()
    res = ctrl.execute(financial_context)
    assert res.status == ControlStatus.PASS
    assert res.severity == SeverityLevel.INFO

def test_price_match_control_higher_price_fail(financial_context):
    po_item = financial_context.po_items[0]
    # Invoiced unit price 1850 vs PO price 1500
    po_item_mock = PurchaseOrderItem(
        id=po_item.id,
        tenant_id=po_item.tenant_id,
        purchase_order_id=po_item.purchase_order_id,
        line_number=1,
        product_code=po_item.product_code,
        description=po_item.description,
        quantity=Decimal("10.0000"),
        unit_price=Decimal("1500.00"),
        line_total=Decimal("15000.00")
    )
    inv_item_mock = InvoiceItem(
        id=financial_context.invoice_items[0].id,
        tenant_id=financial_context.tenant_id,
        invoice_revision_id=financial_context.current_revision.id,
        line_number=1,
        product_code=po_item.product_code,
        description=po_item.description,
        quantity=Decimal("10.0000"),
        unit_price=Decimal("1850.00"), # Price increase!
        line_total=Decimal("18500.00")
    )
    ctx = ControlContext(
        tenant_id=financial_context.tenant_id,
        invoice=financial_context.invoice,
        current_revision=financial_context.current_revision,
        invoice_items=[inv_item_mock],
        vendor=financial_context.vendor,
        purchase_order=financial_context.purchase_order,
        po_items=[po_item_mock],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[],
        tolerance_config=ToleranceConfig(price_variance_percentage_tolerance=Decimal("0.0000"))
    )
    ctrl = PriceMatchControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH
    assert res.variance_value == Decimal("350.00")
    assert res.variance_percentage == Decimal("23.3333")

def test_tax_validation_control_pass(financial_context):
    ctrl = TaxValidationControl()
    res = ctrl.execute(financial_context)
    assert res.status == ControlStatus.PASS

def test_tax_validation_control_math_error_fail(financial_context):
    # Alter tax total on revision to incorrect value
    bad_rev = InvoiceRevision(
        id=financial_context.current_revision.id,
        tenant_id=financial_context.tenant_id,
        invoice_id=financial_context.invoice.id,
        revision_number=1,
        invoice_number="INV-BAD-TAX",
        subtotal=Decimal("100000.00"),
        tax_total=Decimal("15000.00"), # Wrong tax: expected 18% = 18,000!
        discount_total=Decimal("0.00"),
        grand_total=Decimal("115000.00")
    )
    inv_item = InvoiceItem(
        id=financial_context.invoice_items[0].id,
        tenant_id=financial_context.tenant_id,
        invoice_revision_id=bad_rev.id,
        line_number=1,
        quantity=Decimal("100.0000"),
        unit_price=Decimal("1000.00"),
        discount_amount=Decimal("0.00"),
        tax_rate=Decimal("18.0000"), # 18% of 100,000 = 18,000
        tax_amount=Decimal("15000.00"),
        line_total=Decimal("115000.00")
    )
    ctx = ControlContext(
        tenant_id=financial_context.tenant_id,
        invoice=financial_context.invoice,
        current_revision=bad_rev,
        invoice_items=[inv_item],
        vendor=financial_context.vendor,
        purchase_order=financial_context.purchase_order,
        po_items=financial_context.po_items,
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = TaxValidationControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.HIGH
    assert res.variance_value == Decimal("3000.00")

def test_total_validation_control_pass(financial_context):
    ctrl = TotalValidationControl()
    res = ctrl.execute(financial_context)
    assert res.status == ControlStatus.PASS

def test_total_validation_control_math_error_fail(financial_context):
    bad_total_rev = InvoiceRevision(
        id=financial_context.current_revision.id,
        tenant_id=financial_context.tenant_id,
        invoice_id=financial_context.invoice.id,
        revision_number=1,
        invoice_number="INV-BAD-TOTAL",
        subtotal=Decimal("50000.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("9000.00"),
        grand_total=Decimal("64000.00") # 50,000 + 9,000 = 59,000, not 64,000!
    )
    ctx = ControlContext(
        tenant_id=financial_context.tenant_id,
        invoice=financial_context.invoice,
        current_revision=bad_total_rev,
        invoice_items=financial_context.invoice_items,
        vendor=financial_context.vendor,
        purchase_order=financial_context.purchase_order,
        po_items=financial_context.po_items,
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = TotalValidationControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.CRITICAL
    assert res.variance_value == Decimal("5000.00")

def test_payment_terms_control_pass(financial_context):
    ctrl = PaymentTermsControl()
    res = ctrl.execute(financial_context)
    assert res.status == ControlStatus.PASS

def test_payment_terms_control_compressed_warning(financial_context):
    today = date.today()
    compressed_rev = InvoiceRevision(
        id=financial_context.current_revision.id,
        tenant_id=financial_context.tenant_id,
        invoice_id=financial_context.invoice.id,
        revision_number=1,
        invoice_number="INV-COMPRESSED-TERMS",
        invoice_date=today,
        due_date=today + timedelta(days=5), # Demands payment in 5 days vs 30 days!
        subtotal=Decimal("1000.00"),
        grand_total=Decimal("1180.00")
    )
    ctx = ControlContext(
        tenant_id=financial_context.tenant_id,
        invoice=financial_context.invoice,
        current_revision=compressed_rev,
        invoice_items=financial_context.invoice_items,
        vendor=financial_context.vendor,
        purchase_order=financial_context.purchase_order,
        po_items=financial_context.po_items,
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[]
    )
    ctrl = PaymentTermsControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.WARNING
    assert res.severity == SeverityLevel.MEDIUM
    assert "compressing agreed terms" in res.message
