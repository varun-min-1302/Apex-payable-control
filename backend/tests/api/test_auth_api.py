import pytest
from starlette.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "rajesh.sharma@apexfin.in"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "rajesh.sharma@apexfin.in"
    assert "ADMIN" in data["user"]["roles"]

def test_login_invalid_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@apexfin.in"}
    )
    assert response.status_code == 401
    assert "Invalid email" in response.json()["detail"]

def test_get_me_with_bearer_token(client):
    # 1. Login to get token
    login_res = client.post("/api/v1/auth/login", json={"email": "ananya.rao@apexfin.in"})
    token = login_res.json()["access_token"]

    # 2. Query /me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "ananya.rao@apexfin.in"
    assert "FINANCE_MANAGER" in data["roles"]

def test_get_me_with_demo_header(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"X-Demo-User-Email": "rohan.verma@apexfin.in"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "rohan.verma@apexfin.in"
    assert "FINANCE_HEAD" in data["roles"]

def test_list_demo_users(client):
    response = client.get("/api/v1/auth/demo-users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 7
    roles = [u["roles"][0] for u in users]
    assert "ADMIN" in roles
    assert "AP_CLERK" in roles
    assert "FINANCE_MANAGER" in roles
