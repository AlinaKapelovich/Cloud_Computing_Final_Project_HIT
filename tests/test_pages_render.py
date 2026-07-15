"""Every page must render for every role — no server errors, no broken url_for/templates."""
import pytest

from tests.conftest import login

SKIP_ENDPOINTS = {
    "static",
    "auth.logout",                    # would end the session mid-sweep
    "main.uploaded_file",             # needs a filename argument
    "main.prescription_pdf_file",
    "doctor.prescription_pdf_file",
}


def _no_argument_get_routes(app):
    routes = set()
    for rule in app.url_map.iter_rules():
        if rule.endpoint in SKIP_ENDPOINTS or rule.arguments or "GET" not in rule.methods:
            continue
        routes.add(rule.rule)
    return sorted(routes)


@pytest.mark.parametrize("email", ["admin@example.com", "doctor@example.com", "pharmacist@example.com"])
def test_all_pages_render_without_server_errors(app, email):
    client = app.test_client()
    login(client, email)
    for path in _no_argument_get_routes(app):
        response = client.get(path, follow_redirects=True)
        assert response.status_code < 500, f"{email} GET {path} -> {response.status_code}"


def test_error_pages_are_styled(client):
    response = client.get("/definitely-not-a-real-page")
    assert response.status_code == 404
    assert b"404" in response.data
    assert b"styles.css" in response.data  # styled, not a raw Werkzeug page


def test_forbidden_page_is_styled(admin_client):
    response = admin_client.get("/doctor/")
    assert response.status_code == 403
    assert b"Access denied" in response.data
    assert b"styles.css" in response.data


def test_oversized_upload_shows_styled_413(app, pharmacist_client):
    """An upload above MAX_CONTENT_LENGTH must not fall through to Werkzeug's raw page."""
    import io

    app.config["MAX_CONTENT_LENGTH"] = 1024  # 1 KB limit for this test
    oversized = io.BytesIO(b"x" * 5000)
    response = pharmacist_client.post("/pharmacist/upload", data={
        "national_id": "1", "image": (oversized, "big.png"),
    }, content_type="multipart/form-data")

    assert response.status_code == 413
    assert b"File too large" in response.data
    assert b"styles.css" in response.data
