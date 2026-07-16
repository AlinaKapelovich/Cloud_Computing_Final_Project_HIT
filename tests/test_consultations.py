"""Consultation services: valid structure + graceful fallback with no API keys.

The mocked-success tests below exercise each provider's real request/response
handling (Tavily, OpenFDA, ClinicalTrials.gov) without making a real network call —
see tests/conftest.py::block_real_network for why that's safe by default.
"""
from app.models.service_query_log import ServiceQueryLog
from app.services import clinical_trials_service, search_service
from tests.conftest import FakeResponse


def _is_valid_block(block):
    """Every consultation block must always have source/message/results, even on failure."""
    return (
        isinstance(block, dict)
        and "source" in block
        and "message" in block
        and isinstance(block.get("results"), list)
    )


def test_diagnosis_consultation_returns_valid_structure(doctor_client):
    response = doctor_client.post("/api/consult/diagnosis", json={"query": "acute bronchitis"})
    assert response.status_code == 200
    data = response.get_json()
    assert _is_valid_block(data["search"])
    assert _is_valid_block(data["trials"])


def test_side_effects_consultation_returns_valid_structure(pharmacist_client):
    response = pharmacist_client.post("/api/consult/side-effects", json={"query": "amoxicillin"})
    assert response.status_code == 200
    data = response.get_json()
    assert _is_valid_block(data["side_effects"])
    assert _is_valid_block(data["trials"])


def test_empty_query_is_handled_gracefully(doctor_client):
    response = doctor_client.post("/api/consult/diagnosis", json={"query": ""})
    assert response.status_code == 200
    assert response.get_json()["search"]["results"] == []


def test_consultations_are_logged(doctor_client):
    doctor_client.post("/api/consult/diagnosis", json={"query": "asthma"})
    logs = ServiceQueryLog.recent()
    assert len(logs) >= 2  # search + clinical trials
    assert any(log["service"] == "diagnosis_search" for log in logs)


def test_anonymous_users_cannot_consult(client):
    response = client.post("/api/consult/diagnosis", json={"query": "x"})
    assert response.status_code in (401, 302)


def test_clinical_trials_service_never_raises(app):
    """ClinicalTrials.gov must return an empty-but-valid structure on any failure
    (here: the blocked-network fixture, standing in for a real connection error)."""
    with app.test_request_context():
        result = clinical_trials_service.search_trials("anything")
    assert _is_valid_block(result)
    assert result["results"] == []
    assert result["message"]


def test_tavily_success_is_parsed_correctly(app, monkeypatch):
    """Mocked Tavily success: the real request/response handling returns expected results."""
    app.config["TAVILY_API_KEY"] = "fake-tavily-key"

    def fake_post(url, json=None, timeout=None):
        assert url == "https://api.tavily.com/search"
        assert json["api_key"] == "fake-tavily-key"
        assert json["query"] == "acute bronchitis"
        return FakeResponse(200, json_data={"results": [
            {"title": "Bronchitis overview", "content": "Inflammation of the bronchial tubes.",
             "url": "https://example.com/bronchitis"},
        ]})

    monkeypatch.setattr("requests.post", fake_post)

    with app.test_request_context():
        result = search_service.consult_diagnosis("acute bronchitis")

    assert result["source"] == "Tavily"
    assert result["results"][0]["title"] == "Bronchitis overview"
    assert result["message"] is None


def test_openfda_success_is_parsed_correctly(app, monkeypatch):
    """Mocked OpenFDA success (used as the search fallback when Tavily is unavailable)."""
    app.config["TAVILY_API_KEY"] = ""  # forces the OpenFDA fallback path

    def fake_get(url, params=None, timeout=None):
        assert url == "https://api.fda.gov/drug/label.json"
        return FakeResponse(200, json_data={"results": [
            {"openfda": {"brand_name": ["Advil"]}, "indications_and_usage": ["For minor aches and pains."]},
        ]})

    monkeypatch.setattr("requests.get", fake_get)

    with app.test_request_context():
        result = search_service.consult_diagnosis("ibuprofen")

    assert result["source"] == "OpenFDA"
    assert result["results"][0]["title"] == "Advil"


def test_clinical_trials_success_is_parsed_correctly(app, monkeypatch):
    """Mocked ClinicalTrials.gov success: the v2 API response shape is parsed correctly."""

    def fake_get(url, params=None, timeout=None):
        assert url == "https://clinicaltrials.gov/api/v2/studies"
        assert params["query.term"] == "asthma"
        return FakeResponse(200, json_data={"studies": [
            {"protocolSection": {
                "identificationModule": {"nctId": "NCT00000001", "briefTitle": "Asthma Treatment Study"},
                "statusModule": {"overallStatus": "Recruiting"},
            }},
        ]})

    monkeypatch.setattr("requests.get", fake_get)

    with app.test_request_context():
        result = clinical_trials_service.search_trials("asthma")

    assert result["source"] == "ClinicalTrials.gov"
    assert result["results"][0]["nct_id"] == "NCT00000001"
    assert result["results"][0]["status"] == "Recruiting"
    assert "NCT00000001" in result["results"][0]["url"]
