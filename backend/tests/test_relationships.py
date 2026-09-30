import uuid
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from backend.database.models.identity import Tenant, User, Role, UserRole
from backend.database.models.procurement import Vendor, PurchaseOrder, PurchaseOrderItem
from backend.database.models.ap import Invoice, InvoiceRevision, InvoiceItem, PayableLedger
from backend.database.enums import POStatus, ApprovalStatus, InvoiceStatus

def test_foreign_key_vendor_not_found(db_session):
    """Attempting to create a PurchaseOrder with non-existent vendor_id raises foreign key violation."""
    tenant = db_session.query(Tenant).first()
    fake_vendor_id = uuid.uuid4()

    po = PurchaseOrder(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        vendor_id=fake_vendor_id,
        po_number=f"PO-TEST-{uuid.uuid4().hex[:6]}",
        po_date=date.today(),
        currency="INR",
        status=POStatus.DRAFT,
        approval_status=ApprovalStatus.PENDING,
        subtotal=Decimal("1000.00"),
        tax_total=Decimal("180.00"),
        grand_total=Decimal("1180.00")
    )
    db_session.add(po)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "foreign key" in str(exc_info.value).lower()
    db_session.rollback()

def test_foreign_key_tenant_not_found(db_session):
    """Attempting to create an invoice with non-existent tenant_id raises foreign key violation."""
    fake_tenant_id = uuid.uuid4()
    vendor = db_session.query(Vendor).first()

    inv = Invoice(
        id=uuid.uuid4(),
        tenant_id=fake_tenant_id,
        vendor_id=vendor.id,
        invoice_number=f"INV-TEST-{uuid.uuid4().hex[:6]}",
        invoice_date=date.today(),
        due_date=date.today(),
        currency="INR",
        status=InvoiceStatus.RECEIVED
    )
    db_session.add(inv)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "foreign key" in str(exc_info.value).lower()
    db_session.rollback()

def test_user_roles_many_to_many(db_session):
    """Verify that UserRole links User and Role with composite primary key."""
    user = db_session.query(User).first()
    assert user is not None
    assert len(user.user_roles) > 0
    role_names = [ur.role.name for ur in user.user_roles]
    assert any(role_names)

def test_vendor_to_purchase_orders_relationship(db_session):
    """Verify that Vendor navigates to PurchaseOrders."""
    vendor = db_session.query(Vendor).filter(Vendor.purchase_orders.any()).first()
    assert vendor is not None
    assert len(vendor.purchase_orders) > 0
    assert vendor.purchase_orders[0].vendor_id == vendor.id

def test_invoice_to_revisions_and_items_relationship(db_session):
    """Verify that Invoice navigates to revisions and items."""
    invoice = db_session.query(Invoice).filter(Invoice.invoice_number == 'INV-2026-0001').first()
    assert invoice is not None
    assert len(invoice.revisions) >= 1
    rev = invoice.revisions[0]
    assert len(rev.items) >= 1
    assert rev.items[0].invoice_revision_id == rev.id
