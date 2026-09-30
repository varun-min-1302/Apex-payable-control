import pytest
from starlette.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal
from backend.database.models.procurement import Vendor, PurchaseOrder, GoodsReceipt

@pytest.fixture
def client():
    return TestClient(app)

def test_list_vendors(client):
    response = client.get("/api/v1/vendors")
    assert response.status_code == 200
    vendors = response.json()
    assert len(vendors) >= 10
    v = vendors[0]
    assert "vendor_code" in v
    assert "legal_name" in v
    assert "status" in v

def test_get_vendor_detail(client):
    session = SessionLocal()
    vendor = session.query(Vendor).first()
    v_id = str(vendor.id)
    session.close()

    response = client.get(f"/api/v1/vendors/{v_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == v_id
    assert "total_invoices_count" in data
    assert "open_invoices_count" in data

def test_list_purchase_orders(client):
    response = client.get("/api/v1/purchase-orders")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) >= 30
    first = orders[0]
    assert "po_number" in first
    assert "grand_total" in first
    assert len(first["items"]) > 0

def test_get_purchase_order_detail(client):
    session = SessionLocal()
    po = session.query(PurchaseOrder).first()
    po_id = str(po.id)
    session.close()

    response = client.get(f"/api/v1/purchase-orders/{po_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == po_id
    assert len(data["items"]) >= 1

def test_list_goods_receipts(client):
    response = client.get("/api/v1/receipts")
    assert response.status_code == 200
    receipts = response.json()
    assert len(receipts) >= 30
    gr = receipts[0]
    assert "receipt_number" in gr
    assert "status" in gr
    assert len(gr["items"]) > 0
