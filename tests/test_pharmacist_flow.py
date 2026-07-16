"""Pharmacist flow: search, dispense, and upload -> AI validation -> OCR -> review."""
import io

import pytest
from PIL import Image, ImageDraw

from app.models.prescription import Prescription
from app.models.uploaded_prescription import UploadedPrescription


class _Doctor:
    id = "doc-1"
    full_name = "Dr. Test"


@pytest.fixture
def open_prescription(patient):
    return Prescription.create(
        patient=patient, doctor=_Doctor(), diagnosis="Strep throat",
        items=[{"drug_name": "Penicillin", "dosage": "500mg", "frequency": "2x",
                "duration": "10d", "notes": ""}],
    )


def _document_image():
    image = Image.new("RGB", (800, 1000), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 40, 760, 960], outline="black", width=3)
    draw.text((80, 80), "Rx: Ibuprofen 200mg", fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_search_by_national_id_finds_patient(pharmacist_client, patient):
    response = pharmacist_client.get("/pharmacist/search?q=312345678")
    assert response.status_code == 200
    assert b"Yael" in response.data


def test_search_unknown_id_shows_empty_state(pharmacist_client):
    response = pharmacist_client.get("/pharmacist/search?q=000000")
    assert b"No patient found" in response.data


def test_side_effects_consultation_reachable_without_a_patient_search(pharmacist_client):
    """Side-effects consultation is a drug-name lookup, not gated behind a patient
    search — a pharmacist must be able to reach it from a bare /pharmacist/search visit."""
    response = pharmacist_client.get("/pharmacist/search")
    assert response.status_code == 200
    assert b"Drug side-effects consultation" in response.data


def test_pharmacist_sees_prescription_medications(pharmacist_client, open_prescription):
    """The pharmacist must see what they are dispensing, not just a count."""
    response = pharmacist_client.get("/pharmacist/search?q=312345678")
    assert b"Penicillin" in response.data


def test_dispense_open_prescription(pharmacist_client, open_prescription):
    pharmacist_client.post(f"/pharmacist/prescriptions/{open_prescription['id']}/dispense",
                           follow_redirects=True)
    assert Prescription.get_by_id(open_prescription["id"])["status"] == "dispensed"


def test_cannot_dispense_twice(pharmacist_client, open_prescription):
    url = f"/pharmacist/prescriptions/{open_prescription['id']}/dispense"
    pharmacist_client.post(url, follow_redirects=True)
    response = pharmacist_client.post(url, follow_redirects=True)
    assert b"cannot be dispensed" in response.data


def test_upload_runs_validation_then_ocr(pharmacist_client, patient):
    response = pharmacist_client.post("/pharmacist/upload", data={
        "national_id": "312345678", "image": (_document_image(), "rx.png"),
    }, content_type="multipart/form-data")
    assert response.status_code == 302
    upload_id = response.headers["Location"].rstrip("/").split("/")[-1]

    upload = UploadedPrescription.get_by_id(upload_id)
    validation = upload["ai_document_validation_result"]
    # No vision key in tests -> documented heuristic fallback, which should accept this image.
    assert validation["method"] == "heuristic"
    assert validation["valid"] is True
    assert upload["ocr_source"]  # OCR ran (cloud -> tesseract -> manual fallback)
    assert upload["status"] == "open"


def test_review_page_shows_validation_and_ocr(pharmacist_client, patient):
    response = pharmacist_client.post("/pharmacist/upload", data={
        "national_id": "312345678", "image": (_document_image(), "rx.png"),
    }, content_type="multipart/form-data")
    review_url = response.headers["Location"]
    page = pharmacist_client.get(review_url)
    assert page.status_code == 200
    assert b"AI document validation" in page.data
    assert b"OCR" in page.data


def test_ai_validator_rejects_a_non_document(app, pharmacist_client):
    """A tiny/blank file must not pass the heuristic check."""
    from app.services import ai_document_validator

    tiny = io.BytesIO(b"not-an-image")
    upload_dir = app.config["UPLOAD_DIR"]
    path = upload_dir / "tiny.png"
    path.write_bytes(tiny.getvalue())
    with app.test_request_context():
        result = ai_document_validator.validate_document(str(path))
    assert result["valid"] is False


def test_dispense_upload_saves_corrected_text(pharmacist_client, patient):
    response = pharmacist_client.post("/pharmacist/upload", data={
        "national_id": "312345678", "image": (_document_image(), "rx.png"),
    }, content_type="multipart/form-data")
    upload_id = response.headers["Location"].rstrip("/").split("/")[-1]

    pharmacist_client.post(f"/pharmacist/uploaded/{upload_id}/dispense",
                           data={"ocr_text": "Ibuprofen 200mg, 3x/day"}, follow_redirects=True)
    upload = UploadedPrescription.get_by_id(upload_id)
    assert upload["status"] == "dispensed"
    assert upload["ocr_text"] == "Ibuprofen 200mg, 3x/day"
