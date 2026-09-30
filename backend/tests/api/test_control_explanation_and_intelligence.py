"""Tests for Phase 6 Control Intelligence & Explainability.

Verifies:
1. Clean invoice explanation
2. Quantity mismatch explanation
3. Price mismatch explanation
4. Missing PO explanation
5. Duplicate explanation
6. Multiple simultaneous failures explanation
7. No control run (pending) explanation
8. Awaiting approval explanation
9. Payable-created invoice explanation
10. Paid invoice explanation
11. Revision diff ("What Changed?")
12. Audit replay (Chronological timeline)
13. Control Graph (8-stage visual representation)
14. Dashboard Control Health (Real metrics)
15. Tenant isolation
16. RBAC access (Auditors can read)
17. Strict read-only invariant (No state mutations)
"""
from datetime import date
import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.session import SessionLocal
from backend.database.models.identity import User, Tenant
from backend.database.models.procurement import Vendor
from backend.database.models.ap import (
    Invoice,
    InvoiceRevision,
    InvoiceItem,
    ControlRun,
    ControlResult,
    Exception as APException,
    PayableLedger,
)
from backend.database.enums import (
    InvoiceStatus,
    ControlStatus,
    SeverityLevel,
)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# -----------------------------------------------------------------------------
# 1. Clean Invoice Explanation
# -----------------------------------------------------------------------------
def test_clean_invoice_explanation(client, db):
    # Scenario A: Clean 3-way match
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/explanation",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["invoice_id"] == str(inv.id)
    assert data["invoice_number"] == "INV-2026-0001"
    assert len(data["blocking_reasons"]) == 0
    assert data["passed_checks"] > 0


# -----------------------------------------------------------------------------
# 2. Quantity Mismatch Explanation
# -----------------------------------------------------------------------------
def test_quantity_mismatch_explanation(client, db):
    # Scenario B: Quantity Mismatch (Claimed 100 vs GR 80)
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0002").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/explanation",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["can_be_paid"] is False
    assert "Payment blocked" in data["headline"]
    assert len(data["blocking_reasons"]) >= 1

    qty_reason = next(
        (r for r in data["blocking_reasons"] if r["control_code"] in ("QUANTITY_MATCH", "QUANTITY_MISMATCH")),
        None,
    )
    assert qty_reason is not None
    assert "units" in qty_reason["what_happened"].lower() or "quantity" in qty_reason["what_happened"].lower()
    assert len(qty_reason["why_it_matters"]) > 0
    assert len(qty_reason["recommended_action"]) > 0
    assert len(qty_reason["technical_rule"]) > 0


# -----------------------------------------------------------------------------
# 3. Price Mismatch Explanation
# -----------------------------------------------------------------------------
def test_price_mismatch_explanation(client, db):
    # Scenario C: Price Mismatch (Line unit price higher than PO price)
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0003").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/explanation",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["can_be_paid"] is False

    price_reason = next(
        (r for r in data["blocking_reasons"] if r["control_code"] in ("PRICE_MATCH", "PRICE_MISMATCH")),
        None,
    )
    assert price_reason is not None
    assert "price" in price_reason["what_happened"].lower() or "price" in price_reason["title"].lower()
    assert "leakage" in price_reason["why_it_matters"].lower() or "price" in price_reason["why_it_matters"].lower()


# -----------------------------------------------------------------------------
# 4. Missing PO Explanation
# -----------------------------------------------------------------------------
def test_missing_po_explanation(client, db):
    # Scenario D: PO Not Found
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0004").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/explanation",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["can_be_paid"] is False

    po_reason = next(
        (r for r in data["blocking_reasons"] if r["control_code"] in ("PO_EXISTS", "PO_NOT_FOUND")),
        None,
    )
    assert po_reason is not None
    assert "purchase order" in po_reason["title"].lower() or "purchase order" in po_reason["what_happened"].lower()


# -----------------------------------------------------------------------------
# 5. Duplicate Explanation
# -----------------------------------------------------------------------------
def test_duplicate_explanation(client, db):
    # Scenario G: Duplicate Submission
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0007").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/explanation",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["can_be_paid"] is False

    dup_reason = next(
        (r for r in data["blocking_reasons"] if r["control_code"] in ("DUPLICATE_EXACT", "DUPLICATE_INVOICE")),
        None,
    )
    assert dup_reason is not None
    assert "duplicate" in dup_reason["what_happened"].lower() or "duplicate" in dup_reason["title"].lower()


# -----------------------------------------------------------------------------
# 6. Multiple Simultaneous Failures Explanation
# -----------------------------------------------------------------------------
def test_multiple_simultaneous_failures(client, db):
    # Synthetic invoice with 2 failed controls in the same run
    tenant = db.query(Tenant).first()
    user = db.query(User).filter(User.tenant_id == tenant.id).first()
    vendor = db.query(Vendor).filter(Vendor.tenant_id == tenant.id).first()

    multi_inv = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        vendor_id=vendor.id,
        invoice_number=f"INV-MULTI-FAIL-{uuid.uuid4().hex[:6]}",
        invoice_date=date.today(),
        due_date=date.today(),
        status=InvoiceStatus.EXCEPTION.value,
        submitted_by=user.id,
    )
    db.add(multi_inv)
    db.flush()

    rev = InvoiceRevision(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        invoice_id=multi_inv.id,
        revision_number=1,
        invoice_number=multi_inv.invoice_number,
        invoice_date=date.today(),
        due_date=date.today(),
        subtotal=Decimal("50000.00"),
        grand_total=Decimal("59000.00"),
        submitted_by=user.id,
    )
    db.add(rev)
    db.flush()
    multi_inv.current_revision_id = rev.id

    c_run = ControlRun(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        invoice_id=multi_inv.id,
        invoice_revision_id=rev.id,
        run_number=1,
        status="FAILED",
    )
    db.add(c_run)
    db.flush()

    # Add 2 failed results
    res1 = ControlResult(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        control_run_id=c_run.id,
        invoice_id=multi_inv.id,
        control_code="QUANTITY_MATCH",
        control_category="RECEIPT",
        status=ControlStatus.FAIL.value,
        severity=SeverityLevel.HIGH.value,
        variance_value=Decimal("20.00"),
        variance_percentage=Decimal("20.00"),
        message="Quantity mismatch: invoiced 120, received 100",
    )
    res2 = ControlResult(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        control_run_id=c_run.id,
        invoice_id=multi_inv.id,
        control_code="PRICE_MATCH",
        control_category="FINANCIAL",
        status=ControlStatus.FAIL.value,
        severity=SeverityLevel.HIGH.value,
        variance_value=Decimal("250.00"),
        variance_percentage=Decimal("15.00"),
        message="Price mismatch: invoiced 1250, PO 1000",
    )
    db.add(res1)
    db.add(res2)
    db.commit()

    try:
        resp = client.get(
            f"/api/v1/invoices/{multi_inv.id}/explanation",
            headers={"X-Demo-User-Email": user.email},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["blocking_reasons"]) == 2
        codes = [b["control_code"] for b in data["blocking_reasons"]]
        assert "QUANTITY_MATCH" in codes
        assert "PRICE_MATCH" in codes
    finally:
        db.delete(res1)
        db.delete(res2)
        db.delete(c_run)
        db.delete(rev)
        db.delete(multi_inv)
        db.commit()


# -----------------------------------------------------------------------------
# 7. No Control Run (Pending) Explanation
# -----------------------------------------------------------------------------
def test_no_control_run_pending_explanation(client, db):
    tenant = db.query(Tenant).first()
    user = db.query(User).filter(User.tenant_id == tenant.id).first()
    vendor = db.query(Vendor).filter(Vendor.tenant_id == tenant.id).first()

    rec_inv = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        vendor_id=vendor.id,
        invoice_number=f"INV-PENDING-{uuid.uuid4().hex[:6]}",
        invoice_date=date.today(),
        due_date=date.today(),
        status=InvoiceStatus.RECEIVED.value,
        submitted_by=user.id,
    )
    db.add(rec_inv)
    db.commit()

    try:
        resp = client.get(
            f"/api/v1/invoices/{rec_inv.id}/explanation",
            headers={"X-Demo-User-Email": user.email},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["can_be_paid"] is False
        assert "pending" in data["headline"].lower() or "verification" in data["headline"].lower()
        assert len(data["blocking_reasons"]) == 1
        assert data["blocking_reasons"][0]["control_code"] == "CONTROL_RUN_PENDING"
    finally:
        db.delete(rec_inv)
        db.commit()


# -----------------------------------------------------------------------------
# 8. Awaiting Approval Explanation
# -----------------------------------------------------------------------------
def test_awaiting_approval_explanation(client, db):
    # Scenario F: Partial receipt matching, AWAITING_APPROVAL
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0006").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/explanation",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["can_be_paid"] is False
    assert "Waiting for management approval" in data["headline"]
    assert "approval" in data["next_action"].lower() or "approv" in data["next_action"].lower()


# -----------------------------------------------------------------------------
# 9. Payable-Created Invoice Explanation
# -----------------------------------------------------------------------------
def test_payable_created_explanation(client, db):
    # Scenario N: Payable created, partially paid
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0014").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/explanation",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # It is in the payable ledger, so can_be_paid is True
    assert data["can_be_paid"] is True
    assert "payment" in data["headline"].lower() or "approved" in data["headline"].lower()


# -----------------------------------------------------------------------------
# 10. Paid Invoice Explanation
# -----------------------------------------------------------------------------
def test_paid_invoice_explanation(client, db):
    tenant = db.query(Tenant).first()
    user = db.query(User).filter(User.tenant_id == tenant.id).first()
    vendor = db.query(Vendor).filter(Vendor.tenant_id == tenant.id).first()

    paid_inv = Invoice(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        vendor_id=vendor.id,
        invoice_number=f"INV-PAID-TEST-{uuid.uuid4().hex[:6]}",
        invoice_date=date.today(),
        due_date=date.today(),
        status=InvoiceStatus.PAID.value,
        submitted_by=user.id,
    )
    db.add(paid_inv)
    db.commit()

    try:
        resp = client.get(
            f"/api/v1/invoices/{paid_inv.id}/explanation",
            headers={"X-Demo-User-Email": user.email},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["can_be_paid"] is False
        assert "fully paid" in data["headline"].lower()
        assert len(data["blocking_reasons"]) == 0
    finally:
        db.delete(paid_inv)
        db.commit()


# -----------------------------------------------------------------------------
# 11. Revision Diff ("What Changed?")
# -----------------------------------------------------------------------------
def test_revision_diff(client, db):
    # Scenario M: Has Revision 1 and Revision 2
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0013").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/revisions/diff",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_multiple_revisions"] is True
    assert data["revisions_count"] == 2
    assert len(data["diffs"]) == 1
    diff = data["diffs"][0]
    assert diff["from_revision_number"] == 1
    assert diff["to_revision_number"] == 2
    assert diff["controls_rerun"] is True


# -----------------------------------------------------------------------------
# 12. Audit Replay (Chronological timeline)
# -----------------------------------------------------------------------------
def test_audit_replay(client, db):
    # Scenario A invoice has audit trail entries
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/audit-replay",
        headers={"X-Demo-User-Email": "sunita.mehta@apexfin.in"},  # Auditor
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["events_count"] > 0
    timeline = data["timeline"]

    # Verify chronological ordering
    for i in range(1, len(timeline)):
        assert timeline[i]["timestamp"] >= timeline[i - 1]["timestamp"]

    # Verify event structure
    first_event = timeline[0]
    assert "actor_name" in first_event
    assert "title" in first_event
    assert "description" in first_event
    assert "category" in first_event
    assert "technical_details" in first_event


# -----------------------------------------------------------------------------
# 13. Control Graph (8-stage Visual Model)
# -----------------------------------------------------------------------------
def test_control_graph(client, db):
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    assert inv is not None

    resp = client.get(
        f"/api/v1/invoices/{inv.id}/control-graph",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["invoice_id"] == str(inv.id)
    nodes = data["nodes"]
    assert len(nodes) == 8

    node_ids = [n["id"] for n in nodes]
    assert node_ids == ["vendor", "po", "receipt", "financial", "duplicate", "risk", "approval", "payable"]

    # For clean Scenario A, all control nodes should be PASS
    vendor_node = next(n for n in nodes if n["id"] == "vendor")
    assert vendor_node["status"] == "PASS"
    assert vendor_node["passed_count"] >= 2
    assert len(vendor_node["checks"]) == 4


# -----------------------------------------------------------------------------
# 14. Dashboard Control Health
# -----------------------------------------------------------------------------
def test_dashboard_control_health(client, db):
    resp = client.get(
        "/api/v1/dashboard/control-health",
        headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_pass_rate_percentage" in data
    assert data["total_checks_evaluated"] > 0
    assert len(data["categories"]) == 6
    assert "status_breakdown" in data
    assert data["status_breakdown"]["needs_attention"] > 0


# -----------------------------------------------------------------------------
# 15. Tenant Isolation
# -----------------------------------------------------------------------------
def test_tenant_isolation(client, db):
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    assert inv is not None

    # Create temporary Tenant B and User B
    tenant_b = Tenant(name="Tenant B Corp", slug=f"tenant-b-{uuid.uuid4().hex[:6]}", status="ACTIVE")
    db.add(tenant_b)
    db.flush()
    user_b = User(tenant_id=tenant_b.id, email=f"user_b_{uuid.uuid4().hex[:6]}@tenantb.com", full_name="User B", status="ACTIVE")
    db.add(user_b)
    db.commit()

    try:
        # User B cannot access Tenant A explanation
        resp = client.get(
            f"/api/v1/invoices/{inv.id}/explanation",
            headers={"X-Demo-User-Email": user_b.email},
        )
        assert resp.status_code == 404

        # User B cannot access Tenant A control-graph
        resp_cg = client.get(
            f"/api/v1/invoices/{inv.id}/control-graph",
            headers={"X-Demo-User-Email": user_b.email},
        )
        assert resp_cg.status_code == 404

        # User B cannot access Tenant A audit-replay
        resp_ar = client.get(
            f"/api/v1/invoices/{inv.id}/audit-replay",
            headers={"X-Demo-User-Email": user_b.email},
        )
        assert resp_ar.status_code == 404
    finally:
        db.delete(user_b)
        db.delete(tenant_b)
        db.commit()


# -----------------------------------------------------------------------------
# 16. RBAC: Auditor can read explanations and control graphs
# -----------------------------------------------------------------------------
def test_rbac_auditor_access(client, db):
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    assert inv is not None

    # Sunita Mehta is AUDITOR
    for endpoint in ["explanation", "control-graph", "audit-replay", "revisions/diff"]:
        resp = client.get(
            f"/api/v1/invoices/{inv.id}/{endpoint}",
            headers={"X-Demo-User-Email": "sunita.mehta@apexfin.in"},
        )
        assert resp.status_code == 200, f"Auditor failed to read {endpoint}"


# -----------------------------------------------------------------------------
# 17. Invariant: Explanation layer is strictly read-only
# -----------------------------------------------------------------------------
def test_explanation_cannot_mutate_state(client, db):
    inv = db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0002").first()
    status_before = inv.status
    payables_before = db.query(PayableLedger).count()
    exceptions_before = db.query(APException).filter(APException.invoice_id == inv.id).count()

    # Call all Phase 6 explanation endpoints
    client.get(f"/api/v1/invoices/{inv.id}/explanation", headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"})
    client.get(f"/api/v1/invoices/{inv.id}/control-graph", headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"})
    client.get(f"/api/v1/invoices/{inv.id}/audit-replay", headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"})
    client.get(f"/api/v1/invoices/{inv.id}/revisions/diff", headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"})
    client.get("/api/v1/dashboard/control-health", headers={"X-Demo-User-Email": "ananya.rao@apexfin.in"})

    db.refresh(inv)
    assert inv.status == status_before
    assert db.query(PayableLedger).count() == payables_before
    assert db.query(APException).filter(APException.invoice_id == inv.id).count() == exceptions_before
