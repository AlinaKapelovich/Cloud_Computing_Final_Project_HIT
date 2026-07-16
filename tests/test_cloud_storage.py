"""cloud_storage_service.py — mocked Cloudinary success + local fallback.

No real network call is made: cloudinary.uploader.upload is monkeypatched directly
(the Cloudinary SDK, not the `requests` module, so it isn't covered by the
conftest.py network block — this test exercises that path explicitly).
"""
from pathlib import Path

from app.services import cloud_storage_service


def test_pdf_uses_local_fallback_when_cloudinary_not_configured(app, tmp_path):
    pdf_path = tmp_path / "prescription_abc.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    with app.test_request_context():
        result = cloud_storage_service.store_pdf(pdf_path, "abc")

    assert result["storage"] == "local"
    assert result["url"] and "/prescriptions/file/" in result["url"]


def test_pdf_uploads_to_cloudinary_when_configured(app, monkeypatch, tmp_path):
    app.config.update(
        CLOUDINARY_CLOUD_NAME="demo-cloud",
        CLOUDINARY_API_KEY="fake-key",
        CLOUDINARY_API_SECRET="fake-secret",
    )
    pdf_path = tmp_path / "prescription_xyz.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    captured = {}

    def fake_upload(path, resource_type=None, public_id=None, overwrite=None):
        captured["path"] = path
        captured["public_id"] = public_id
        return {"secure_url": "https://res.cloudinary.com/demo-cloud/raw/upload/prescription_xyz.pdf"}

    import cloudinary.uploader

    monkeypatch.setattr(cloudinary.uploader, "upload", fake_upload)
    monkeypatch.setattr("cloudinary.config", lambda **kwargs: None)

    with app.test_request_context():
        result = cloud_storage_service.store_pdf(pdf_path, "xyz")

    assert result["storage"] == "cloudinary"
    assert result["url"] == "https://res.cloudinary.com/demo-cloud/raw/upload/prescription_xyz.pdf"
    assert captured["path"] == str(pdf_path)
    assert captured["public_id"] == "medcloud/prescriptions/xyz"
