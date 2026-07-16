"""Role-based access control on the consultation API endpoints (task G).

Permissions are enforced in the backend controller (role_required), not only by
hiding buttons in templates — these tests hit the routes directly regardless of UI.
"""


def test_doctor_can_access_diagnosis_consultation(doctor_client):
    response = doctor_client.post("/api/consult/diagnosis", json={"query": "asthma"})
    assert response.status_code == 200


def test_pharmacist_cannot_access_diagnosis_consultation(pharmacist_client):
    response = pharmacist_client.post("/api/consult/diagnosis", json={"query": "asthma"})
    assert response.status_code == 403


def test_admin_cannot_access_diagnosis_consultation(admin_client):
    response = admin_client.post("/api/consult/diagnosis", json={"query": "asthma"})
    assert response.status_code == 403


def test_pharmacist_can_access_side_effects_consultation(pharmacist_client):
    response = pharmacist_client.post("/api/consult/side-effects", json={"query": "ibuprofen"})
    assert response.status_code == 200


def test_doctor_cannot_access_side_effects_consultation(doctor_client):
    response = doctor_client.post("/api/consult/side-effects", json={"query": "ibuprofen"})
    assert response.status_code == 403


def test_admin_cannot_access_side_effects_consultation(admin_client):
    response = admin_client.post("/api/consult/side-effects", json={"query": "ibuprofen"})
    assert response.status_code == 403
