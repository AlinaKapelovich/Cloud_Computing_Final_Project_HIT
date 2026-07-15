"""ocr_service.py — extract text from a handwritten/scanned prescription image.

Strategy (fallback chain):
  1. Cloud OCR API (OCR_API_URL, e.g. a HuggingFace/PaddleOCR-VL endpoint) — cloud-first.
  2. Local Tesseract (pytesseract) if the Tesseract binary is installed.
  3. Manual transcription: return empty text with a clear message so the pharmacist
     can type the text in themselves.

Returns: {"text": str, "source": str, "message": str|None}. Never raises.
"""
import logging

import requests

from flask import current_app

log = logging.getLogger(__name__)
TIMEOUT = 20


def extract_text(image_path: str) -> dict:
    """Extract text from the image, degrading gracefully through the fallback chain."""
    url = current_app.config.get("OCR_API_URL")
    if url:
        result = _cloud_ocr(image_path, url)
        if result is not None:
            return result

    result = _tesseract(image_path)
    if result is not None:
        return result

    return {
        "text": "",
        "source": "manual",
        "message": "Automatic OCR is unavailable. Please transcribe the prescription text manually below.",
    }


def _cloud_ocr(image_path: str, url: str):
    """POST the image to a cloud OCR endpoint. Returns a dict, or None on failure."""
    key = current_app.config.get("OCR_API_KEY")
    try:
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        with open(image_path, "rb") as handle:
            response = requests.post(url, headers=headers, files={"file": handle}, timeout=TIMEOUT)
        response.raise_for_status()
        # Accept either JSON {"text": ...} or a plain-text body.
        try:
            data = response.json()
            text = data.get("text") or data.get("result") or ""
        except ValueError:
            text = response.text
        return {"text": (text or "").strip(), "source": "Cloud OCR",
                "message": None if text else "Cloud OCR returned no text."}
    except Exception as exc:  # noqa: BLE001 - fall back to Tesseract.
        log.warning("Cloud OCR failed: %s", exc)
        return None


def _tesseract(image_path: str):
    """Run local Tesseract OCR. Returns a dict, or None if unavailable."""
    if image_path.lower().endswith(".pdf"):
        return None  # Tesseract path here handles images only.
    try:
        import pytesseract
        from PIL import Image

        with Image.open(image_path) as img:
            text = pytesseract.image_to_string(img)
        return {"text": (text or "").strip(), "source": "Tesseract (local)",
                "message": None if text.strip() else "Tesseract found no readable text."}
    except Exception as exc:  # noqa: BLE001 - binary or library missing -> manual fallback.
        log.warning("Tesseract OCR unavailable: %s", exc)
        return None
