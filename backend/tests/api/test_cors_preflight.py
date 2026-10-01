import pytest
from starlette.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

PROD_ORIGIN = "https://apex-payable-control.vercel.app"
DISALLOWED_ORIGIN = "https://unauthorized-third-party.com"

def test_cors_get_from_production_origin(client):
    """Verify standard GET requests from the exact production origin receive CORS headers."""
    response = client.get(
        "/health",
        headers={"Origin": PROD_ORIGIN}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_options_preflight_from_production_origin(client):
    """Verify preflight OPTIONS requests from production origin are handled successfully."""
    response = client.options(
        "/api/v1/demo-users",
        headers={
            "Origin": PROD_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type, x-demo-user-email, authorization, accept",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"
    
    allowed_methods = response.headers.get("access-control-allow-methods", "").upper()
    for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]:
        assert method in allowed_methods

    allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
    for header in ["content-type", "x-demo-user-email", "authorization", "accept"]:
        assert header in allowed_headers

def test_cors_x_demo_user_email_accepted_with_persona(client):
    """Verify X-Demo-User-Email custom header is accepted during preflight and live invocation."""
    # 1. Preflight OPTIONS for endpoint with custom header
    preflight = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": PROD_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-demo-user-email, content-type",
        }
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert "x-demo-user-email" in preflight.headers.get("access-control-allow-headers", "").lower()

    # 2. Live request with custom header
    response = client.get(
        "/",
        headers={
            "Origin": PROD_ORIGIN,
            "X-Demo-User-Email": "ananya.rao@apexfin.in",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"
    data = response.json()
    assert data["status"] == "OPERATIONAL"

def test_cors_disallowed_origin_rejected(client):
    """Verify disallowed origins fail preflight and do not receive allow-origin header."""
    # Preflight from disallowed origin
    preflight = client.options(
        "/health",
        headers={
            "Origin": DISALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        }
    )
    assert preflight.status_code == 400
    assert preflight.headers.get("access-control-allow-origin") is None

    # Normal GET from disallowed origin
    response = client.get(
        "/health",
        headers={"Origin": DISALLOWED_ORIGIN}
    )
    assert response.headers.get("access-control-allow-origin") is None

def test_cors_options_preflight_post_mutation(client):
    """Verify preflight OPTIONS for POST mutations (e.g. invoice actions)."""
    response = client.options(
        "/api/v1/invoices",
        headers={
            "Origin": PROD_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, authorization, x-demo-user-email",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert "POST" in response.headers.get("access-control-allow-methods", "").upper()
