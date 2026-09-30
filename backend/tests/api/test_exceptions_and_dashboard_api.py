import pytest
from starlette.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal
from backend.database.models.ap import Exception as APException, Invoice

@pytest.fixture
def client():
    return TestClient(app)

def test_list_exceptions(client):
    response = client.get("/api/v1/exceptions?status=OPEN")
    assert response.status_code == 200
    exceptions = response.json()
    assert len(exceptions) >= 0

def test_resolve_exception(client):
    session = SessionLocal()
    inv = session.query(Invoice).filter(Invoice.invoice_number == "INV-2026-0002").first()
    exc = APException(
        tenant_id=inv.tenant_id,
        invoice_id=inv.id,
        exception_code="TEST_RESOLUTION_EXC",
        title="Test Resolution Exception",
        description="Test exception for resolution API test",
        severity="MEDIUM",
        status="OPEN",
    )
    session.add(exc)
    session.commit()
    exc_id = str(exc.id)
    session.close()

    try:
        response = client.post(
            f"/api/v1/exceptions/{exc_id}/resolve",
            json={"action": "RESOLVE", "reason": "Vendor sent approved credit note CN-2026-0044."},
            headers={"X-Demo-User-Email": "vikram.malhotra@apexfin.in"}  # Procurement Manager
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESOLVED"
        assert data["resolution_reason"] == "Vendor sent approved credit note CN-2026-0044."
    finally:
        session = SessionLocal()
        created_exc = session.query(APException).filter(APException.id == exc_id).first()
        if created_exc:
            session.delete(created_exc)
        orig_exc = session.query(APException).filter(
            APException.invoice_id == inv.id,
            APException.exception_code == "QUANTITY_MISMATCH"
        ).first()
        if orig_exc:
            orig_exc.status = "OPEN"
            orig_exc.resolution_reason = None
        inv_record = session.query(Invoice).filter(Invoice.id == inv.id).first()
        if inv_record:
            inv_record.status = "EXCEPTION"
        session.commit()
        session.close()

def test_get_dashboard_kpis(client):
    response = client.get("/api/v1/dashboard/kpis")
    assert response.status_code == 200
    kpis = response.json()
    assert kpis["total_invoices"] >= 40
    assert kpis["open_exceptions"] >= 0
    assert float(kpis["three_way_match_pass_rate_percentage"]) > 0

def test_get_dashboard_scenarios(client):
    response = client.get("/api/v1/dashboard/scenarios")
    assert response.status_code == 200
    data = response.json()
    scenarios = data["scenarios"]
    assert len(scenarios) == 15
    codes = [s["scenario_code"] for s in scenarios]
    assert "Scenario A" in codes
    assert "Scenario B" in codes
    assert "Scenario G" in codes
    assert "Scenario O" in codes

def test_list_audit_logs(client):
    response = client.get("/api/v1/audit/logs?limit=20")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) > 0
    first = logs[0]
    assert "action" in first
    assert "entity_type" in first
    assert "created_at" in first
