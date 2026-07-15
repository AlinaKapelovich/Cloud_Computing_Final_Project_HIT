"""cloud_storage_service.py — store generated prescription PDFs.

Purpose: upload a generated PDF to Cloudinary (cloud object storage) and return a
public URL that we persist in MongoDB.

Cloud concept: object/blob storage as a managed cloud service (Storage-as-a-Service).

Fallback: if Cloudinary credentials are missing or the upload fails, we keep the PDF
locally under generated_pdfs/ and serve it through the app instead. The feature never
breaks — it degrades to local storage.
"""
import logging

from flask import current_app, url_for

log = logging.getLogger(__name__)


def _cloudinary_configured() -> bool:
    cfg = current_app.config
    return bool(cfg.get("CLOUDINARY_CLOUD_NAME") and cfg.get("CLOUDINARY_API_KEY") and cfg.get("CLOUDINARY_API_SECRET"))


def store_pdf(local_path, public_id: str) -> dict:
    """Store the PDF and return {storage, url, path}.

    storage is "cloudinary" when the cloud upload succeeded, otherwise "local".
    """
    local_path = str(local_path)

    if _cloudinary_configured():
        try:
            import cloudinary
            import cloudinary.uploader

            cfg = current_app.config
            cloudinary.config(
                cloud_name=cfg["CLOUDINARY_CLOUD_NAME"],
                api_key=cfg["CLOUDINARY_API_KEY"],
                api_secret=cfg["CLOUDINARY_API_SECRET"],
                secure=True,
            )
            result = cloudinary.uploader.upload(
                local_path,
                resource_type="auto",  # PDFs are handled as raw/image by Cloudinary.
                public_id=f"medcloud/prescriptions/{public_id}",
                overwrite=True,
            )
            url = result.get("secure_url")
            log.info("Uploaded prescription PDF to Cloudinary: %s", url)
            return {"storage": "cloudinary", "url": url, "path": local_path}
        except Exception as exc:  # noqa: BLE001 - fall back to local storage on any error.
            log.warning("Cloudinary upload failed (%s). Falling back to local storage.", exc)

    # Local fallback: expose the file through our own download route.
    # Note: this route lives on the shared `main` blueprint so that doctors AND
    # pharmacists can both open the PDF (a doctor-only route would 403 pharmacists).
    filename = str(local_path).replace("\\", "/").split("/")[-1]
    try:
        local_url = url_for("main.prescription_pdf_file", filename=filename)
    except Exception:  # noqa: BLE001 - url_for may fail outside a request context.
        local_url = None
    return {"storage": "local", "url": local_url, "path": local_path}
