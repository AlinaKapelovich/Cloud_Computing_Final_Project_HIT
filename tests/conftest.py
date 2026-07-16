"""Shared pytest fixtures.

Each test gets a fresh application (and therefore a fresh in-memory database), so tests
are isolated and need no cloud credentials. CSRF is disabled for the test client only.

Network policy: the `block_real_network` autouse fixture below replaces `requests.post`
and `requests.get` with a stub that raises if called, so the *standard* `python -m
pytest` run can never make a real outbound HTTP call to Tavily, OpenFDA, ClinicalTrials.gov,
a cloud OCR endpoint, or a hosted vision endpoint — even on a machine with real internet
access and even if real API keys happen to be present in the environment. Individual
tests that need to exercise a provider's success/failure path re-patch `requests.post`/
`requests.get` themselves (via the `monkeypatch` fixture, which layers on top of and
later undoes this default). This also means every external-service code path degrades to
its documented fallback by default, so the existing "graceful fallback" tests keep working
unchanged — they are simply exercising the block instead of a real network failure.

Tesseract policy: the `block_real_tesseract` autouse fixture below forces
`ocr_service._tesseract()` to return None (as if the binary were not installed), so the
standard suite never depends on whether Tesseract happens to be installed on the machine
running it — it deterministically exercises the manual-transcription fallback instead.
Tests marked `@pytest.mark.integration` opt out of both blocks and may exercise the real
binary/network; they are excluded from the default `pytest` run (see pytest.ini's
`addopts = -m "not integration"`) and must be run explicitly with `pytest -m integration`.
"""
import pytest

from app import create_app

DEMO_PASSWORD = "demo1234"


class FakeResponse:
    """A minimal stand-in for `requests.Response`, used to mock external APIs in tests."""

    def __init__(self, status_code=200, json_data=None, text_data="", content=b""):
        self.status_code = status_code
        self._json = json_data
        self.text = text_data
        self.content = content

    def json(self):
        if self._json is None:
            raise ValueError("Response has no JSON body")
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"{self.status_code} error")


def _blocked_network_call(*_args, **_kwargs):
    raise RuntimeError(
        "Real network access is disabled during tests. Explicitly monkeypatch "
        "requests.post/requests.get in this test if you need to exercise a specific "
        "provider response."
    )


@pytest.fixture(autouse=True)
def block_real_network(request, monkeypatch):
    """Prevent any test from making a real outbound HTTP call unless it opts in."""
    if "integration" in request.keywords:
        return
    monkeypatch.setattr("requests.post", _blocked_network_call)
    monkeypatch.setattr("requests.get", _blocked_network_call)


@pytest.fixture(autouse=True)
def block_real_tesseract(request, monkeypatch):
    """Prevent the standard suite from depending on whether Tesseract is installed.

    Forces app.services.ocr_service._tesseract() to return None unconditionally, so
    every non-integration test deterministically exercises the manual-transcription
    fallback rather than an environment-dependent real/absent Tesseract binary.
    """
    if "integration" in request.keywords:
        return
    monkeypatch.setattr("app.services.ocr_service._tesseract", lambda image_path: None)


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
