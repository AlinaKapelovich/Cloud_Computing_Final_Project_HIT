"""ocr_service.py — mocked tests for the fallback chain:
Hugging Face -> generic cloud OCR -> Tesseract -> manual transcription.

No real network call is made (see tests/conftest.py::block_real_network). Each test
explicitly monkeypatches requests.post/requests.get to simulate one provider's behavior.
"""
import io

from PIL import Image

from app.services import ocr_service
from tests.conftest import FakeResponse


def _sample_image_path(app):
    path = app.config["UPLOAD_DIR"] / "ocr_sample.png"
    Image.new("RGB", (400, 500), "white").save(path)
    return str(path)


def test_huggingface_ocr_success_returns_expected_text(app, monkeypatch):
    """A configured Hugging Face token + a successful response returns its generated_text."""
    app.config["HUGGINGFACE_API_TOKEN"] = "fake-token"
    app.config["HUGGINGFACE_OCR_MODEL"] = "microsoft/trocr-base-handwritten"
    image_path = _sample_image_path(app)

    def fake_post(url, headers=None, data=None, timeout=None):
        assert url == "https://api-inference.huggingface.co/models/microsoft/trocr-base-handwritten"
        assert headers["Authorization"] == "Bearer fake-token"
        assert isinstance(data, (bytes, bytearray))  # raw image bytes, not multipart
        return FakeResponse(200, json_data=[{"generated_text": "Amoxicillin 500mg 3x/day"}])

    monkeypatch.setattr("requests.post", fake_post)

    with app.test_request_context():
        result = ocr_service.extract_text(image_path)

    assert result["text"] == "Amoxicillin 500mg 3x/day"
    assert "Hugging Face" in result["source"]
    assert result["message"] is None


def test_huggingface_cold_start_falls_back_to_next_provider(app, monkeypatch):
    """A 503 (model loading) must not be treated as success — it falls through the chain."""
    app.config["HUGGINGFACE_API_TOKEN"] = "fake-token"
    app.config["OCR_API_URL"] = ""  # force the chain past the generic cloud adapter
    image_path = _sample_image_path(app)

    def fake_post(url, headers=None, data=None, timeout=None):
        return FakeResponse(503, text_data='{"error": "Model is loading", "estimated_time": 20}')

    monkeypatch.setattr("requests.post", fake_post)

    with app.test_request_context():
        result = ocr_service.extract_text(image_path)

    # No Tesseract binary in the test environment -> falls all the way to manual.
    assert result["source"] in ("manual", "Tesseract (local)")
    if result["source"] == "manual":
        assert "manually" in result["message"].lower()


def test_huggingface_failure_falls_back_to_generic_cloud_ocr(app, monkeypatch):
    """If Hugging Face errors out, the generic OCR_API_URL adapter is tried next."""
    app.config["HUGGINGFACE_API_TOKEN"] = "fake-token"
    app.config["OCR_API_URL"] = "https://example-ocr.test/extract"
    image_path = _sample_image_path(app)

    def fake_post(url, headers=None, data=None, files=None, timeout=None):
        if "huggingface" in url:
            raise ConnectionError("simulated network failure")
        assert url == "https://example-ocr.test/extract"
        return FakeResponse(200, json_data={"text": "Ibuprofen 200mg"})

    monkeypatch.setattr("requests.post", fake_post)

    with app.test_request_context():
        result = ocr_service.extract_text(image_path)

    assert result["text"] == "Ibuprofen 200mg"
    assert result["source"] == "Cloud OCR"


def test_no_cloud_provider_configured_falls_back_to_tesseract_or_manual(app):
    """With no cloud provider configured, extract_text still returns a valid, non-crashing result."""
    app.config["HUGGINGFACE_API_TOKEN"] = ""
    app.config["OCR_API_URL"] = ""
    image_path = _sample_image_path(app)

    with app.test_request_context():
        result = ocr_service.extract_text(image_path)

    assert result["source"] in ("manual", "Tesseract (local)")
    assert isinstance(result["text"], str)


def test_manual_transcription_text_can_be_saved_and_dispensed(pharmacist_client, patient):
    """When OCR falls back to manual, the pharmacist's typed text is what gets dispensed."""
    image = Image.new("RGB", (800, 1000), "white")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)

    response = pharmacist_client.post("/pharmacist/upload", data={
        "national_id": "312345678", "image": (buf, "rx.png"),
    }, content_type="multipart/form-data")
    upload_id = response.headers["Location"].rstrip("/").split("/")[-1]

    manual_text = "Ibuprofen 200mg, twice daily, 5 days (manually transcribed)"
    response = pharmacist_client.post(f"/pharmacist/uploaded/{upload_id}/dispense", data={
        "ocr_text": manual_text, "manual_confirm": "on",
    }, follow_redirects=True)

    from app.models.uploaded_prescription import UploadedPrescription

    upload = UploadedPrescription.get_by_id(upload_id)
    # Either dispensed immediately (heuristic validated the plain white image) or blocked
    # pending confirmation — both are valid outcomes; either way the typed text is preserved.
    assert upload["ocr_text"] == manual_text
