"""Admin patient management (create, list, edit, detail, validation)."""
from app.models.patient import Patient


def test_create_patient_and_view_profile(admin_client, patient):
    assert patient is not None
    response = admin_client.get(f"/admin/patients/{patient['id']}")
    assert response.status_code == 200
    assert b"Patient profile" in response.data
    assert b"Yael" in response.data


def test_age_is_calculated_from_birth_date_not_stored(patient):
    # We store birth_date and derive age, so it can never go stale.
    assert patient["birth_date"] == "1990-05-14"
    assert isinstance(patient["age"], int)
    assert patient["age"] > 30


def test_duplicate_national_id_is_rejected(admin_client, patient):
    response = admin_client.post("/admin/patients/new", data={
        "national_id": "312345678", "first_name": "Dup", "last_name": "Licate",
        "gender": "male", "birth_date": "1980-01-01",
    }, follow_redirects=True)
    assert b"already exists" in response.data
    assert Patient.count() == 1


def test_patient_appears_in_list(admin_client, patient):
    response = admin_client.get("/admin/patients")
    assert response.status_code == 200
    assert b"Yael" in response.data


def test_empty_list_shows_empty_state(admin_client):
    response = admin_client.get("/admin/patients")
    assert b"No patients yet" in response.data


def test_edit_patient_updates_fields(admin_client, patient):
    response = admin_client.post(f"/admin/patients/{patient['id']}/edit", data={
        "national_id": "312345678", "first_name": "Yael", "last_name": "Barr",
        "gender": "female", "birth_date": "1990-05-14",
        "email": "yael@example.com", "phone": "+972500000000",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert Patient.get_by_national_id("312345678")["last_name"] == "Barr"


def test_invalid_form_is_rejected(admin_client):
    response = admin_client.post("/admin/patients/new", data={
        "national_id": "", "first_name": "", "last_name": "",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert Patient.count() == 0
