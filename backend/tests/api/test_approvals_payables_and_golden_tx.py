import pytest
from starlette.testclient import TestClient
from datetime import date, timedelta
from decimal import Decimal
import uuid

from backend.main import app
from backend.database.session import SessionLocal
from backend.database.models.ap import Invoice, InvoiceRevision, Approval, PayableLedger, ApprovalPolicy, Payment
from backend.database.models.procurement import Vendor, PurchaseOrder
from backend.database.models.identity import Tenant
from backend.database.enums import ApprovalStatus, InvoiceStatus, PayableStatus

@pytest.fixture
def client():
    return TestClient(app)

def test_ap_clerk_cannot_decide_approval(client):
    """RBAC test: AP_CLERK does not have managerial approval authority."""
    session = SessionLocal()
    appr = session.query(Approval).first()
    appr_id = str(appr.id)
    session.close()

    response = client.post(
        f"/api/v1/approvals/{appr_id}/decide",
        json={"decision": "APPROVE", "comments": "Unauthorized clerk attempt"},
        headers={"X-Demo-User-Email": "priya.nair@apexfin.in"}  # AP Clerk
    )
    assert response.status_code == 403
    assert "Operation requires one of the following roles" in response.json()["detail"]

def test_golden_transaction_approval_creates_payable(client):
    """
    CRITICAL WORKFLOW TEST (The Golden Transaction):
    1. A verified invoice has a pending approval request.
    2. Finance Manager reviews and submits APPROVE.
    3. The system atomically commits the invoice to ap.payable_ledger.
    4. Invoice status transitions to PAYABLE_CREATED.
    """
    session = SessionLocal()
    tenant = session.query(Tenant).first()
    vendor = session.query(Vendor).first()
    po = session.query(PurchaseOrder).first()
    policy = session.query(ApprovalPolicy).filter(ApprovalPolicy.tenant_id == tenant.id).first()
    today = date.today()

    inv_num = f"INV-GOLDEN-{uuid.uuid4().hex[:6]}"
    inv = Invoice(
        tenant_id=tenant.id,
        vendor_id=vendor.id,
        purchase_order_id=po.id,
        invoice_number=inv_num,
        invoice_date=today,
        due_date=today + timedelta(days=30),
        currency="INR",
        status=InvoiceStatus.AWAITING_APPROVAL.value,
        source_type="API_UPLOAD",
    )
    session.add(inv)
    session.flush()

    rev = InvoiceRevision(
        tenant_id=tenant.id,
        invoice_id=inv.id,
        revision_number=1,
        invoice_number=inv_num,
        invoice_date=today,
        due_date=today + timedelta(days=30),
        subtotal=Decimal("50000.00"),
        tax_total=Decimal("9000.00"),
        grand_total=Decimal("59000.00"),
    )
    session.add(rev)
    session.flush()

    inv.current_revision_id = rev.id
    appr = Approval(
        tenant_id=tenant.id,
        invoice_id=inv.id,
        approval_policy_id=policy.id,
        sequence_order=1,
        status=ApprovalStatus.PENDING.value,
    )
    session.add(appr)
    session.commit()

    appr_id = str(appr.id)
    inv_id = str(inv.id)
    session.close()

    # Finance Manager approves
    response = client.post(
        f"/api/v1/approvals/{appr_id}/decide",
        json={"decision": "APPROVE", "comments": "3-way match verified. Approved for disbursement."},
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"}  # Finance Manager
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "APPROVE"
    assert data["payable_created"] is True
    assert data["payable_number"] is not None
    assert data["invoice_status"] == "PAYABLE_CREATED"

    # Verify via Payables API
    payable_id = data["payable_id"]
    pay_res = client.get(f"/api/v1/payables/{payable_id}")
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert pay_data["status"] == "OPEN"
    assert float(pay_data["approved_amount"]) > 0
    assert float(pay_data["remaining_balance"]) > 0

    # Record partial disbursement
    pay_ref = f"NEFT-TEST-{uuid.uuid4().hex[:8].upper()}"
    disburse_res = client.post(
        f"/api/v1/payables/{payable_id}/payments",
        json={
            "amount": 10000.00,
            "payment_reference": pay_ref,
            "payment_method": "NEFT"
        },
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"}
    )
    assert disburse_res.status_code == 201
    disb_data = disburse_res.json()
    assert float(disb_data["amount"]) == 10000.00
    assert disb_data["payment_reference"] == pay_ref

    # Check updated payable status is PARTIALLY_PAID
    updated_pay = client.get(f"/api/v1/payables/{payable_id}").json()
    assert updated_pay["status"] == "PARTIALLY_PAID"
    assert float(updated_pay["paid_amount"]) == 10000.00
