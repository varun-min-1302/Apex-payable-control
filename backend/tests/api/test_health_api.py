import pytest
from starlette.testclient import TestClient
from backend.main import app, sanitize_error_message

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check_endpoint_contract(client):
    """Test that /health returns proper contract and status codes."""
    for path in ["/health", "/api/v1/health"]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data
        assert data["status"] in ["HEALTHY", "UNHEALTHY"]
        assert data["database"] in ["CONNECTED", "DISCONNECTED"]

        if data["status"] == "UNHEALTHY":
            assert "diagnostics" in data
            diag = data["diagnostics"]
            assert "exception_class" in diag
            assert "error_message" in diag
            assert "database_url_configured" in diag
            assert diag["can_create_connection"] is False

def test_health_check_never_exposes_credentials(client):
    """Verify that credentials and raw database passwords are never exposed in /health response."""
    response = client.get("/health")
    assert response.status_code == 200
    raw_text = response.text.lower()
    
    # Sensitive tokens must never appear
    assert "password=" not in raw_text
    assert "jwt_secret" not in raw_text
    assert "gemini_api_key" not in raw_text

def test_sanitize_error_message_strips_passwords_and_tokens():
    """Verify regex sanitization correctly masks sensitive connection details."""
    raw_url_err = "failed to connect: postgresql+psycopg2://admin:superSecret123@aws-0.supabase.com:6543/postgres"
    sanitized = sanitize_error_message(raw_url_err)
    assert "superSecret123" not in sanitized
    assert ":***@" in sanitized

    raw_param_err = "connection params: host=db.example.com password=mySecretPass user=postgres"
    sanitized_param = sanitize_error_message(raw_param_err)
    assert "mySecretPass" not in sanitized_param
    assert "password=***" in sanitized_param

    raw_token_err = "failed with token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    sanitized_token = sanitize_error_message(raw_token_err)
    assert "eyJhbGci" not in sanitized_token
    assert "token=***" in sanitized_token
