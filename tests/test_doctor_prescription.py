"""Doctor flow: visit -> prescription -> PDF generation and storage."""
import os

from app.models.prescription import Prescription
from tests.conftest import login


def _create_prescription(doctor_client, patient):
    """Drive the real doctor flow and return the created prescription document."""
    response = doctor_client.post(f"/doctor/patients/{patient['id']}/visit",
                                  data={"complaints": "Cough and fever", "diagnosis": "Acute bronchitis"})
    assert response.status_code == 302
    visit_url = response.headers["Location"]

    response = doctor_client.post(visit_url, data={
        "diagnosis": "Acute bronchitis",
        "item_drug": ["Amoxicillin", "Paracetamol"],
        "item_dosage": ["500 mg", "500 mg"],
        "item_frequency": ["3x/day", "as needed"],
        "item_duration": ["7 days", "5 days"],
        "item_notes": ["after meals", ""],
    })
    assert response.status_code == 302
    prescription_id = response.headers["Location"].rstrip("/").split("/")[-1]
    return Prescription.get_by_id(prescription_id)


def test_doctor_can_select_patient(doctor_client, patient):
    response = doctor_client.get("/doctor/patients")
    assert response.status_code == 200
    assert b"Yael" in response.data


def test_visit_and_prescription_with_items(doctor_client, patient):
    prescription = _create_prescription(doctor_client, patient)
    assert len(prescription["items"]) == 2
    assert prescription["items"][0]["drug_name"] == "Amoxicillin"
    assert prescription["status"] == "open"
    assert prescription["source"] == "digital"


def test_pdf_is_generated_and_stored_locally_without_cloudinary(doctor_client, patient):
    prescription = _create_prescription(doctor_client, patient)
    assert prescription["pdf_path"]
    assert os.path.exists(prescription["pdf_path"])
    # No Cloudinary credentials in tests -> documented local fallback.
    assert prescription["pdf_storage"] == "local"
    assert prescription["pdf_url"]


def test_prescription_detail_page_shows_items(doctor_client, patient):
    prescription = _create_prescription(doctor_client, patient)
    response = doctor_client.get(f"/doctor/prescriptions/{prescription['id']}")
    assert b"Amoxicillin" in response.data


def test_prescription_without_medications_is_rejected(doctor_client, patient):
    response = doctor_client.post(f"/doctor/patients/{patient['id']}/visit",
                                  data={"complaints": "c", "diagnosis": "d"})
    visit_url = response.headers["Location"]
    response = doctor_client.post(visit_url, data={"diagnosis": "d", "item_drug": [""]},
                                  follow_redirects=True)
    assert b"at least one medication" in response.data


def test_pharmacist_can_open_locally_stored_pdf(app, doctor_client, patient):
    """Regression: the PDF link shown on the pharmacist page must not be doctor-only."""
    prescription = _create_prescription(doctor_client, patient)

    pharmacist = app.test_client()
    login(pharmacist, "pharmacist@example.com")
    assert pharmacist.get(prescription["pdf_url"]).status_code == 200


def test_legacy_doctor_pdf_url_still_works_for_pharmacist(app, doctor_client, patient):
    """Old /doctor/prescriptions/file/... links redirect to the shared route."""
    prescription = _create_prescription(doctor_client, patient)
    filename = prescription["pdf_path"].replace("\\", "/").split("/")[-1]

    pharmacist = app.test_client()
    login(pharmacist, "pharmacist@example.com")
    response = pharmacist.get(f"/doctor/prescriptions/file/{filename}", follow_redirects=True)
    assert response.status_code == 200
