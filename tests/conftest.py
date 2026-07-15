"""Shared pytest fixtures.

Each test gets a fresh application (and therefore a fresh in-memory database), so tests
are isolated and need no cloud credentials. CSRF is disabled for the test client only.
"""
import pytest

from app import create_app

DEMO_PASSWORD = "demo1234"


@pytest.fixture
def app():
    application = create_app()
    application.config.update(WTF_CSRF_ENABLED=False, TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, password=DEMO_PASSWORD):
    """Log a test client in and return the response."""
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


@pytest.fixture
def admin_client(app):
    c = app.test_client()
    login(c, "admin@example.com")
    return c


@pytest.fixture
def doctor_client(app):
    c = app.test_client()
    login(c, "doctor@example.com")
    return c


@pytest.fixture
def pharmacist_client(app):
    c = app.test_client()
    login(c, "pharmacist@example.com")
    return c


@pytest.fixture
def patient(admin_client):
    """Create and return a patient via the real Admin flow."""
    from app.models.patient import Patient

    admin_client.post("/admin/patients/new", data={
        "national_id": "312345678", "first_name": "Yael", "last_name": "Bar",
        "gender": "female", "birth_date": "1990-05-14",
        "email": "yael@example.com", "phone": "+972500000000",
    }, follow_redirects=True)
    return Patient.get_by_national_id("312345678")
