"""ocr_service.py — extract text from a handwritten/scanned prescription image.

Strategy (fallback chain):
  1. **Hugging Face Inference API** running a TrOCR handwritten-text model
     (HUGGINGFACE_API_TOKEN) — the concrete, implemented cloud OCR provider for this
     project. Default model: microsoft/trocr-base-handwritten.
  2. A generic cloud OCR endpoint (OCR_API_URL) — an escape hatch if a different
     provider is configured instead of/alongside Hugging Face.
  3. Local Tesseract (pytesseract) if the Tesseract binary is installed.
  4. Manual transcription: return empty text with a clear message so the pharmacist
     can type the text in themselves.

Returns: {"text": str, "source": str, "message": str|None}. Never raises.

Honesty note: this provider's request/response handling is implemented against the
real, documented Hugging Face Inference API contract, but it has not been exercised
against the live API with a real token in this environment (no outbound network
access here — see docs/CLOUD_SERVICES.md). It is covered by mocked unit tests instead.
"""
import logging

import requests

from flask import current_app

log = logging.getLogger(__name__)
TIMEOUT = 20
HF_INFERENCE_BASE_URL = "https://api-inference.huggingface.co/models"


def extract_text(image_path: str) -> dict:
    """Extract text from the image, degrading gracefully through the fallback chain."""
    is_pdf = image_path.lower().endswith(".pdf")

    if not is_pdf:  # the TrOCR model expects an image, not a PDF.
        result = _huggingface_ocr(image_path)
        if result is not None:
            return result

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


def _huggingface_ocr(image_path: str):
    """Call the Hugging Face Inference API running a TrOCR handwritten-text model.

    Provider contract (Hugging Face Inference API, image-to-text pipeline):
      - POST https://api-inference.huggingface.co/models/<model_id>
      - Header: Authorization: Bearer <token>
      - Body: raw image bytes (no multipart wrapper, no JSON envelope)
      - Success response: a JSON list, e.g. [{"generated_text": "..."}]
      - Cold-start response: HTTP 503 with {"error": "...loading...", "estimated_time": n}
        (the shared model server had to spin up — treated as a transient failure so we
        fall back to the next provider rather than making the pharmacist wait).

    Returns a result dict, or None to fall through to the next provider in the chain
    (no token configured, network error, or a non-2xx response).
    """
    token = current_app.config.get("HUGGINGFACE_API_TOKEN")
    if not token:
        return None

    model_id = current_app.config.get("HUGGINGFACE_OCR_MODEL", "microsoft/trocr-base-handwritten")
    url = f"{HF_INFERENCE_BASE_URL}/{model_id}"

    try:
        with open(image_path, "rb") as handle:
            image_bytes = handle.read()

        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            data=image_bytes,
            timeout=TIMEOUT,
        )

        if response.status_code == 503:
            log.warning("Hugging Face OCR model is cold-starting (503): %s", response.text[:200])
            return None

        response.raise_for_status()
        payload = response.json()

        if isinstance(payload, list) and payload and "generated_text" in payload[0]:
            text = payload[0]["generated_text"]
        elif isinstance(payload, dict) and "error" in payload:
            log.warning("Hugging Face OCR returned an error payload: %s", payload["error"])
            return None
        else:
            log.warning("Hugging Face OCR returned an unexpected response shape: %r", payload)
            text = ""

        text = (text or "").strip()
        return {
            "text": text,
            "source": f"Hugging Face ({model_id})",
            "message": None if text else "Hugging Face OCR returned no text.",
        }
    except Exception as exc:  # noqa: BLE001 - fall back to the next provider.
        log.warning("Hugging Face OCR request failed: %s", exc)
        return None


def _cloud_ocr(image_path: str, url: str):
    """POST the image to a generic cloud OCR endpoint. Returns a dict, or None on failure."""
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
