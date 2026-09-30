import uuid
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from backend.database.models.identity import Tenant, User
from backend.database.models.procurement import Vendor, PurchaseOrder
from backend.database.models.ap import Invoice
from backend.database.enums import (
    TenantStatus, VendorStatus, VendorRiskStatus, POStatus, ApprovalStatus, InvoiceStatus
)

def test_tenant_vendor_code_uniqueness_within_same_tenant(db_session):
    """Enforce UNIQUE(tenant_id, vendor_code): cannot duplicate vendor_code within same tenant."""
    tenant = db_session.query(Tenant).first()
    vendor = db_session.query(Vendor).filter(Vendor.tenant_id == tenant.id).first()

    dup_vendor = Vendor(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        vendor_code=vendor.vendor_code, # Duplicate within same tenant!
        legal_name="Duplicate Vendor Ltd",
        display_name="Duplicate Vendor",
        tax_identifier="27AAAAA0000A1Z5",
        status=VendorStatus.ACTIVE,
        risk_status=VendorRiskStatus.NORMAL
    )
    db_session.add(dup_vendor)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "uq_procurement_vendors_tenant_vendor_code" in str(exc_info.value) or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()

def test_tenant_po_number_uniqueness_within_same_tenant(db_session):
    """Enforce UNIQUE(tenant_id, po_number): cannot duplicate po_number within same tenant."""
    po = db_session.query(PurchaseOrder).first()

    dup_po = PurchaseOrder(
        id=uuid.uuid4(),
        tenant_id=po.tenant_id,
        vendor_id=po.vendor_id,
        po_number=po.po_number, # Duplicate within same tenant!
        po_date=po.po_date,
        currency="INR",
        status=POStatus.DRAFT,
        approval_status=ApprovalStatus.PENDING,
        subtotal=Decimal("100.00"),
        tax_total=Decimal("18.00"),
        grand_total=Decimal("118.00")
    )
    db_session.add(dup_po)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.flush()
    assert "uq_procurement_pos_tenant_po_number" in str(exc_info.value) or "unique constraint" in str(exc_info.value).lower()
    db_session.rollback()

def test_cross_tenant_isolation_and_duplicate_code_allowance(db_session):
    """
    Verify cross-tenant isolation:
    Different tenants CAN use the same vendor_code and invoice_number without conflict.
    """
    # Create a secondary tenant
    tenant2 = Tenant(
        id=uuid.uuid4(),
        name="Beta Logistics Corp",
        slug=f"beta-logistics-{uuid.uuid4().hex[:4]}",
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant2)
    db_session.flush()

    existing_vendor = db_session.query(Vendor).first()

    # Create vendor in tenant2 with identical vendor_code as tenant1
    vendor_t2 = Vendor(
        id=uuid.uuid4(),
        tenant_id=tenant2.id,
        vendor_code=existing_vendor.vendor_code, # Identical code in different tenant
        legal_name="Tenant 2 Clone Vendor Pvt",
        display_name="Clone Vendor",
        tax_identifier="33AAAAA1111A1Z1",
        status=VendorStatus.ACTIVE,
        risk_status=VendorRiskStatus.NORMAL
    )
    db_session.add(vendor_t2)
    db_session.flush()

    assert vendor_t2.id != existing_vendor.id
    assert vendor_t2.vendor_code == existing_vendor.vendor_code
    assert vendor_t2.tenant_id != existing_vendor.tenant_id

    # Create invoice in tenant2 with identical invoice_number as tenant1
    existing_invoice = db_session.query(Invoice).first()

    invoice_t2 = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant2.id,
        vendor_id=vendor_t2.id,
        invoice_number=existing_invoice.invoice_number, # Identical invoice number in different tenant
        invoice_date=existing_invoice.invoice_date,
        due_date=existing_invoice.due_date,
        currency="INR",
        status=InvoiceStatus.RECEIVED
    )
    db_session.add(invoice_t2)
    db_session.flush()

    assert invoice_t2.id != existing_invoice.id
    assert invoice_t2.invoice_number == existing_invoice.invoice_number
    assert invoice_t2.tenant_id != existing_invoice.tenant_id

    # Clean rollback so test session remains unchanged
    db_session.rollback()
