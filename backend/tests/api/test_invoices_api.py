import pytest
from starlette.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal
from backend.database.models.procurement import Vendor
from backend.database.models.ap import Invoice

@pytest.fixture
def client():
    return TestClient(app)

def test_list_invoices(client):
    response = client.get("/api/v1/invoices?limit=10")
    assert response.status_code == 200
    invoices = response.json()
    assert len(invoices) == 10
    first = invoices[0]
    assert "invoice_number" in first
    assert "status" in first
    assert "grand_total" in first

def test_list_invoices_filtered_by_status(client):
    response = client.get("/api/v1/invoices?status=EXCEPTION")
    assert response.status_code == 200
    invoices = response.json()
    assert len(invoices) > 0
    assert all(inv["status"] == "EXCEPTION" for inv in invoices)

def test_get_invoice_detail(client):
    session = SessionLocal()
    inv = session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    inv_id = str(inv.id)
    session.close()

    response = client.get(f"/api/v1/invoices/{inv_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["invoice_number"] == "INV-2026-0001"
    assert data["current_revision"] is not None
    assert len(data["current_revision"]["items"]) > 0

def test_trigger_control_run_endpoint(client):
    session = SessionLocal()
    inv = session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    inv_id = str(inv.id)
    orig_status = inv.status
    session.close()

    try:
        response = client.post(
            f"/api/v1/invoices/{inv_id}/control-runs",
            headers={"X-Demo-User-Email": "priya.nair@apexfin.in"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_controls"] == 18
        assert data["passed_count"] >= 15
        assert data["status"] in ("PASSED", "WARNING")
    finally:
        session = SessionLocal()
        inv_to_restore = session.query(Invoice).filter(Invoice.id == inv_id).first()
        if inv_to_restore:
            inv_to_restore.status = orig_status
            session.commit()
        session.close()

def test_get_invoice_control_results_endpoint(client):
    session = SessionLocal()
    inv = session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0001").first()
    inv_id = str(inv.id)
    session.close()

    response = client.get(f"/api/v1/invoices/{inv_id}/control-results")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 10
    codes = [r["control_code"] for r in results]
    assert "PRICE_MATCH" in codes
    assert "QUANTITY_MATCH" in codes
    assert "VENDOR_EXISTS" in codes

def test_create_invoice_shell(client):
    session = SessionLocal()
    vendor = session.query(Vendor).first()
    v_id = str(vendor.id)
    session.close()

    import uuid
    inv_num = f"INV-TEST-NEW-{uuid.uuid4().hex[:6]}"
    payload = {
        "vendor_id": v_id,
        "invoice_number": inv_num,
        "invoice_date": "2026-04-10",
        "due_date": "2026-05-10",
        "currency": "INR",
        "items": [
            {
                "line_number": 1,
                "product_code": "PROD-A",
                "description": "Enterprise Cloud Database Server",
                "quantity": 2.0,
                "unit_of_measure": "EA",
                "unit_price": 50000.0,
                "tax_rate": 0.18
            }
        ]
    }
    response = client.post(
        "/api/v1/invoices",
        json=payload,
        headers={"X-Demo-User-Email": "priya.nair@apexfin.in"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["invoice_number"] == inv_num
    assert data["status"] == "RECEIVED"
    assert float(data["grand_total"]) == 118000.0
