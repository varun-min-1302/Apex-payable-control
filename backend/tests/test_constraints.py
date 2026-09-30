import uuid
from decimal import Decimal
from datetime import date, datetime, timezone
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, InternalError
from backend.database.models.identity import Tenant, User
from backend.database.models.procurement import Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem
from backend.database.models.ap import Invoice, InvoiceRevision, InvoiceItem, PayableLedger, ControlRun
from backend.database.models.audit import AuditLog
from backend.database.enums import (
    TenantStatus, UserStatus, VendorStatus, VendorRiskStatus,
    POStatus, ApprovalStatus, ReceiptStatus, InvoiceStatus,
    ExtractionStatus, ControlRunStatus, PayableStatus
)

def test_purchase_order_item_positive_quantity_constraint(db_session):
    """Verify that purchase_order_items enforces quantity > 0."""
    tenant = db_session.query(Tenant).first()
    vendor = db_session.query(Vendor).first()
    po = db_session.query(PurchaseOrder).first()

    item = PurchaseOrderItem(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        purchase_order_id=po.id,
        line_number=999,
        description="Invalid Quantity Item",
        quantity=Decimal("0.0000"),
        unit_of_measure="NOS",
        unit_price=Decimal("100.00"),
        tax_rate=Decimal("18.0000"),
        tax_amount=Decimal("0.00"),
        line_total=Decimal("0.00")
    )
    db_session.add(item)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "ck_procurement_po_items_quantity" in str(exc_info.value) or "check constraint" in str(exc_info.value).lower()
    db_session.rollback()

def test_purchase_order_item_non_negative_price_constraint(db_session):
    """Verify that purchase_order_items enforces unit_price >= 0."""
    tenant = db_session.query(Tenant).first()
    po = db_session.query(PurchaseOrder).first()

    item = PurchaseOrderItem(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        purchase_order_id=po.id,
        line_number=998,
        description="Negative Price Item",
        quantity=Decimal("5.0000"),
        unit_of_measure="NOS",
        unit_price=Decimal("-10.00"),
        tax_rate=Decimal("18.0000"),
        tax_amount=Decimal("0.00"),
        line_total=Decimal("-50.00")
    )
    db_session.add(item)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "ck_procurement_po_items_price" in str(exc_info.value) or "check constraint" in str(exc_info.value).lower()
    db_session.rollback()

def test_goods_receipt_accepted_plus_rejected_constraint(db_session):
    """Verify that goods_receipt_items enforces accepted_quantity + rejected_quantity <= received_quantity."""
    tenant = db_session.query(Tenant).first()
    gr = db_session.query(GoodsReceipt).first()
    po_item = db_session.query(PurchaseOrderItem).first()

    gr_item = GoodsReceiptItem(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        goods_receipt_id=gr.id,
        purchase_order_item_id=po_item.id,
        received_quantity=Decimal("10.0000"),
        accepted_quantity=Decimal("8.0000"),
        rejected_quantity=Decimal("5.0000"), # 8 + 5 = 13 > 10!
        notes="Over accepted"
    )
    db_session.add(gr_item)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "ck_procurement_gr_items_accepted_rejected" in str(exc_info.value) or "check constraint" in str(exc_info.value).lower()
    db_session.rollback()

def test_invoice_item_positive_quantity_constraint(db_session):
    """Verify that invoice_items enforces quantity > 0."""
    tenant = db_session.query(Tenant).first()
    inv_rev = db_session.query(InvoiceRevision).first()

    inv_item = InvoiceItem(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        invoice_revision_id=inv_rev.id,
        line_number=999,
        description="Zero Quantity Invoice Item",
        quantity=Decimal("0.0000"),
        unit_of_measure="NOS",
        unit_price=Decimal("50.00"),
        tax_rate=Decimal("18.0000"),
        tax_amount=Decimal("0.00"),
        line_total=Decimal("0.00")
    )
    db_session.add(inv_item)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "ck_ap_invoice_items_quantity" in str(exc_info.value) or "check constraint" in str(exc_info.value).lower()
    db_session.rollback()

def test_audit_logs_immutable_update_trigger(db_session):
    """Verify that trg_prevent_audit_log_modification blocks UPDATE on audit.audit_logs."""
    log = db_session.query(AuditLog).first()
    assert log is not None

    with pytest.raises((InternalError, IntegrityError)) as exc_info:
        db_session.execute(
            text(f"UPDATE audit.audit_logs SET action = 'HACKED' WHERE id = '{log.id}'")
        )
        db_session.flush()
    assert "append-only" in str(exc_info.value).lower()
    db_session.rollback()

def test_audit_logs_immutable_delete_trigger(db_session):
    """Verify that trg_prevent_audit_log_modification blocks DELETE on audit.audit_logs."""
    log = db_session.query(AuditLog).first()
    assert log is not None

    with pytest.raises((InternalError, IntegrityError)) as exc_info:
        db_session.execute(
            text(f"DELETE FROM audit.audit_logs WHERE id = '{log.id}'")
        )
        db_session.flush()
    assert "append-only" in str(exc_info.value).lower()
    db_session.rollback()

def test_payable_ledger_unique_invoice_id(db_session):
    """Verify that payable_ledger strictly enforces unique invoice_id per tenant."""
    payable = db_session.query(PayableLedger).first()
    assert payable is not None

    # Attempt to create a duplicate payable ledger entry for the same invoice
    duplicate_payable = PayableLedger(
        id=uuid.uuid4(),
        tenant_id=payable.tenant_id,
        invoice_id=payable.invoice_id,
        invoice_revision_id=payable.invoice_revision_id,
        vendor_id=payable.vendor_id,
        payable_number=f"PAY-DUP-{uuid.uuid4().hex[:6]}",
        approved_amount=payable.approved_amount,
        currency="INR",
        due_date=date.today(),
        status="OPEN",
        approved_at=datetime.now(timezone.utc)
    )
    db_session.add(duplicate_payable)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "uq_payable_ledger_tenant_invoice" in str(exc_info.value) or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()

def test_invoice_revisions_unique_number_per_invoice(db_session):
    """Verify that invoice_revisions enforces UNIQUE(invoice_id, revision_number)."""
    rev = db_session.query(InvoiceRevision).first()
    assert rev is not None

    dup_rev = InvoiceRevision(
        id=uuid.uuid4(),
        tenant_id=rev.tenant_id,
        invoice_id=rev.invoice_id,
        revision_number=rev.revision_number, # Duplicate revision number!
        invoice_number=rev.invoice_number,
        invoice_date=date.today(),
        due_date=date.today(),
        currency="INR",
        subtotal=Decimal("100.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("18.00"),
        grand_total=Decimal("118.00")
    )
    db_session.add(dup_rev)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "uq_invoice_revisions_invoice_rev_num" in str(exc_info.value) or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()
