"""AI document validator — enforcement at dispense time (task H).

Four required states:
  1. valid       -> dispensing is allowed normally.
  2. invalid     -> dispensing is blocked; a different image must be uploaded.
  3. unavailable, no manual confirmation -> dispensing is blocked.
  4. unavailable, with manual confirmation -> dispensing is allowed, and the
     confirmation (who + when) is recorded.
"""
import io

from PIL import Image

from app.models.uploaded_prescription import UploadedPrescription
from app.services import ai_document_validator


def _upload(pharmacist_client, patient, image_bytes, filename="rx.png"):
    buf = io.BytesIO(image_bytes)
    response = pharmacist_client.post("/pharmacist/upload", data={
        "national_id": patient["national_id"], "image": (buf, filename),
    }, content_type="multipart/form-data")
    upload_id = response.headers["Location"].rstrip("/").split("/")[-1]
    return upload_id


def _valid_document_bytes():
    image = Image.new("RGB", (800, 1000), "white")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_valid_document_dispenses_normally(pharmacist_client, patient):
    upload_id = _upload(pharmacist_client, patient, _valid_document_bytes())
    upload = UploadedPrescription.get_by_id(upload_id)
    assert upload["ai_document_validation_result"]["valid"] is True

    pharmacist_client.post(f"/pharmacist/uploaded/{upload_id}/dispense",
                           data={"ocr_text": "text"}, follow_redirects=True)
    assert UploadedPrescription.get_by_id(upload_id)["status"] == "dispensed"


def test_invalid_document_blocks_dispensing(pharmacist_client, patient):
    """A file too small to be a real document must be rejected, not silently dispensed."""
    tiny_png = b"\x89PNG\r\n\x1a\n" + b"0" * 20  # well under the 1024-byte heuristic floor
    upload_id = _upload(pharmacist_client, patient, tiny_png, filename="tiny.png")
    upload = UploadedPrescription.get_by_id(upload_id)
    assert upload["ai_document_validation_result"]["valid"] is False

    response = pharmacist_client.post(f"/pharmacist/uploaded/{upload_id}/dispense",
                                      data={"ocr_text": "text"}, follow_redirects=True)

    assert b"cannot be dispensed" in response.data or b"different image" in response.data
    assert UploadedPrescription.get_by_id(upload_id)["status"] == "open"


def test_unavailable_validation_blocks_dispensing_without_confirmation(
    pharmacist_client, patient, monkeypatch
):
    """When the validator can't decide, dispensing must not proceed as if nothing happened."""
    monkeypatch.setattr(
        ai_document_validator, "validate_document",
        lambda path: {"valid": None, "method": "unavailable", "message": "no reader available", "details": {}},
    )
    upload_id = _upload(pharmacist_client, patient, _valid_document_bytes())
    upload = UploadedPrescription.get_by_id(upload_id)
    assert upload["ai_document_validation_result"]["valid"] is None
    assert upload["manual_confirmed"] is False

    response = pharmacist_client.post(f"/pharmacist/uploaded/{upload_id}/dispense",
                                      data={"ocr_text": "text"}, follow_redirects=True)

    assert b"manually confirm" in response.data
    assert UploadedPrescription.get_by_id(upload_id)["status"] == "open"


def test_unavailable_validation_dispenses_with_manual_confirmation(
    pharmacist_client, patient, monkeypatch
):
    """Checking the manual-confirmation box unblocks dispensing and records who/when."""
    monkeypatch.setattr(
        ai_document_validator, "validate_document",
        lambda path: {"valid": None, "method": "unavailable", "message": "no reader available", "details": {}},
    )
    upload_id = _upload(pharmacist_client, patient, _valid_document_bytes())

    response = pharmacist_client.post(f"/pharmacist/uploaded/{upload_id}/dispense", data={
        "ocr_text": "text", "manual_confirm": "on",
    }, follow_redirects=True)

    upload = UploadedPrescription.get_by_id(upload_id)
    assert upload["status"] == "dispensed"
    assert upload["manual_confirmed"] is True
    assert upload["manual_confirmed_by"] == "Pharmacist Noa Levi"
    assert upload["manual_confirmed_at"] is not None
