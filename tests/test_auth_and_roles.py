"""Authentication, role-based access control, and health/API endpoints."""
from tests.conftest import login


def test_health_endpoint_reports_database_mode(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert response.get_json()["database"]


def test_api_ping(client):
    assert client.get("/api/ping").status_code == 200


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"MedCloud" in response.data


def test_invalid_credentials_are_rejected(client):
    response = login(client, "admin@example.com", "wrong-password")
    assert b"Invalid email or password" in response.data


def test_each_role_reaches_its_own_dashboard(app):
    expected = {
        "admin@example.com": b"Admin dashboard",
        "doctor@example.com": b"Doctor dashboard",
        "pharmacist@example.com": b"Pharmacist dashboard",
    }
    for email, marker in expected.items():
        c = app.test_client()
        assert marker in login(c, email).data


def test_role_isolation_returns_403(admin_client):
    assert admin_client.get("/doctor/").status_code == 403
    assert admin_client.get("/pharmacist/").status_code == 403


def test_unauthenticated_user_is_redirected_to_login(client):
    response = client.get("/admin/", follow_redirects=True)
    assert b"Log in" in response.data or b"Sign in" in response.data


def test_passwords_are_stored_hashed_not_plaintext(app):
    from app.models.user import User

    user = User.get_by_email("admin@example.com")
    assert user.password_hash
    assert "demo1234" not in user.password_hash
    assert user.check_password("demo1234")
