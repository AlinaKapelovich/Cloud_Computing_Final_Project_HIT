"""Consultation services: valid structure + graceful fallback with no API keys."""
from app.models.service_query_log import ServiceQueryLog


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
    """ClinicalTrials.gov must return an empty-but-valid structure on failure."""
    from app.services import clinical_trials_service

    with app.test_request_context():
        app.config["CLINICAL_TRIALS_BASE_URL"] = "http://127.0.0.1:9/unreachable"
        result = clinical_trials_service.search_trials("anything")
    assert _is_valid_block(result)
    assert result["results"] == []
    assert result["message"]
