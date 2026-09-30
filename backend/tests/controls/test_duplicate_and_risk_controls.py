import uuid
from decimal import Decimal
import pytest
from backend.domain.controls.duplicate_controls import DuplicateInvoiceControl, SemanticDuplicateControl
from backend.domain.controls.risk_controls import ThresholdProximityControl, UnusualAmountControl
from backend.domain.controls.base import ControlContext
from backend.application.dto.control_dto import ToleranceConfig
from backend.database.models.identity import Tenant
from backend.database.models.procurement import Vendor
from backend.database.models.ap import Invoice, InvoiceRevision, ApprovalPolicy
from backend.database.enums import ControlStatus, SeverityLevel

@pytest.fixture
def risk_context(db_session):
    tenant = db_session.query(Tenant).first()
    vendor = db_session.query(Vendor).first()
    invoice = db_session.query(Invoice).first()
    revision = invoice.revisions[0]
    policies = list(db_session.query(ApprovalPolicy).filter(ApprovalPolicy.tenant_id == tenant.id).all())
    historical = list(db_session.query(Invoice).filter(Invoice.tenant_id == tenant.id).all())

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
        approval_policies=policies,
        historical_invoices=historical,
        tolerance_config=ToleranceConfig()
    )

def test_duplicate_control_pass(risk_context):
    # Context with empty historical list
    ctx = ControlContext(
        tenant_id=risk_context.tenant_id,
        invoice=risk_context.invoice,
        current_revision=risk_context.current_revision,
        invoice_items=risk_context.invoice_items,
        vendor=risk_context.vendor,
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[],
        historical_invoices=[]
    )
    ctrl = DuplicateInvoiceControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.PASS
    assert res.severity == SeverityLevel.INFO

def test_duplicate_control_doc_hash_collision_fail(risk_context):
    doc_hash = "abc123hashidentical"
    inv1 = Invoice(
        id=uuid.uuid4(),
        tenant_id=risk_context.tenant_id,
        vendor_id=risk_context.vendor.id,
        invoice_number="INV-ORIG",
        document_hash=doc_hash
    )
    inv2 = Invoice(
        id=uuid.uuid4(),
        tenant_id=risk_context.tenant_id,
        vendor_id=risk_context.vendor.id,
        invoice_number="INV-DUP",
        document_hash=doc_hash # Duplicate document hash!
    )
    ctx = ControlContext(
        tenant_id=risk_context.tenant_id,
        invoice=inv2,
        current_revision=risk_context.current_revision,
        invoice_items=risk_context.invoice_items,
        vendor=risk_context.vendor,
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[],
        historical_invoices=[inv1]
    )
    ctrl = DuplicateInvoiceControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.CRITICAL
    assert "Exact document hash collision detected" in res.message

def test_duplicate_control_vendor_invoice_number_fail(risk_context):
    inv1 = Invoice(
        id=uuid.uuid4(),
        tenant_id=risk_context.tenant_id,
        vendor_id=risk_context.vendor.id,
        invoice_number="INV-SHARED-NUM",
        document_hash="hash1"
    )
    inv2 = Invoice(
        id=uuid.uuid4(),
        tenant_id=risk_context.tenant_id,
        vendor_id=risk_context.vendor.id,
        invoice_number="INV-SHARED-NUM", # Same vendor and invoice number!
        document_hash="hash2"
    )
    ctx = ControlContext(
        tenant_id=risk_context.tenant_id,
        invoice=inv2,
        current_revision=risk_context.current_revision,
        invoice_items=risk_context.invoice_items,
        vendor=risk_context.vendor,
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[],
        historical_invoices=[inv1]
    )
    ctrl = DuplicateInvoiceControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.FAIL
    assert res.severity == SeverityLevel.CRITICAL
    assert "Duplicate invoice number" in res.message

def test_semantic_duplicate_control_returns_not_applicable(risk_context):
    """
    CRITICAL INSTRUCTION CHECK:
    Vector embeddings table currently has 0 rows.
    Must return NOT_APPLICABLE honestly without fabricating artificial scores.
    """
    ctrl = SemanticDuplicateControl()
    res = ctrl.execute(risk_context)
    assert res.status == ControlStatus.NOT_APPLICABLE
    assert res.severity == SeverityLevel.INFO
    assert "NOT_APPLICABLE" in res.message
    assert res.actual_value.get("vector_embeddings_available") is False

def test_threshold_proximity_control_trigger(risk_context):
    # Tier policy with max_amount = 100,000
    mock_policy = ApprovalPolicy(
        id=uuid.uuid4(),
        tenant_id=risk_context.tenant_id,
        name="Tier 2 Finance Manager Approval",
        min_amount=Decimal("10000.00"),
        max_amount=Decimal("100000.00"),
        required_role="FINANCE_MANAGER",
        sequence_order=1,
        active=True
    )
    # Invoice with ₹99,800.00 (within ₹200 / 0.2% of threshold)
    prox_rev = InvoiceRevision(
        id=uuid.uuid4(),
        tenant_id=risk_context.tenant_id,
        invoice_id=risk_context.invoice.id,
        revision_number=1,
        invoice_number="INV-PROX",
        subtotal=Decimal("84576.27"),
        tax_total=Decimal("15223.73"),
        grand_total=Decimal("99800.00")
    )
    ctx = ControlContext(
        tenant_id=risk_context.tenant_id,
        invoice=risk_context.invoice,
        current_revision=prox_rev,
        invoice_items=risk_context.invoice_items,
        vendor=risk_context.vendor,
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[mock_policy],
        tolerance_config=ToleranceConfig(
            threshold_proximity_percentage=Decimal("2.00"),
            threshold_proximity_absolute_amount=Decimal("5000.00")
        )
    )
    ctrl = ThresholdProximityControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.WARNING
    assert res.severity == SeverityLevel.MEDIUM
    assert "Threshold proximity warning" in res.message
    assert res.variance_value == Decimal("200.00")

def test_unusual_amount_control_insufficient_history(risk_context):
    """With fewer than 3 historical invoices, returns NOT_APPLICABLE without fabricating stats."""
    ctx = ControlContext(
        tenant_id=risk_context.tenant_id,
        invoice=risk_context.invoice,
        current_revision=risk_context.current_revision,
        invoice_items=risk_context.invoice_items,
        vendor=risk_context.vendor,
        purchase_order=None,
        po_items=[],
        goods_receipts=[],
        goods_receipt_items=[],
        approval_policies=[],
        historical_invoices=[] # 0 history
    )
    ctrl = UnusualAmountControl()
    res = ctrl.execute(ctx)
    assert res.status == ControlStatus.NOT_APPLICABLE
    assert "minimum 3 required" in res.message
