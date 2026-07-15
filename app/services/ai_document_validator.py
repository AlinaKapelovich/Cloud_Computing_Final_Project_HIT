"""ai_document_validator.py — check an upload looks like a real prescription/document.

Bonus feature. Runs BEFORE OCR so we don't waste OCR on junk uploads.

Strategy (fallback chain):
  1. Hosted vision model (VISION_API_URL + VISION_API_KEY) — "AI as a service".
  2. Local heuristics (Pillow): the file opens as an image, has a sensible size,
     readable dimensions and a document-like aspect ratio.
  3. If neither is possible, mark validation as unavailable and require the
     pharmacist to confirm manually. The upload flow never crashes.

Returns: {"valid": bool|None, "method": str, "message": str, "details": dict}.
"""
import logging
import os

import requests

from flask import current_app

log = logging.getLogger(__name__)
TIMEOUT = 10


def validate_document(image_path: str) -> dict:
    """Validate that the uploaded file looks like a document/prescription."""
    url = current_app.config.get("VISION_API_URL")
    if url:
        result = _hosted_vision(image_path, url)
        if result is not None:
            return result

    return _heuristic(image_path)


def _hosted_vision(image_path: str, url: str):
    """Call a hosted vision model. Returns a result dict, or None on failure."""
    key = current_app.config.get("VISION_API_KEY")
    try:
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        with open(image_path, "rb") as handle:
            response = requests.post(url, headers=headers, files={"file": handle}, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        # We accept a flexible response shape: {is_document: bool, confidence: float}.
        is_document = bool(data.get("is_document", data.get("valid", True)))
        return {
            "valid": is_document,
            "method": "hosted_vision",
            "message": "Validated by hosted vision model." if is_document
                       else "The uploaded image does not appear to be a prescription.",
            "details": {"confidence": data.get("confidence")},
        }
    except Exception as exc:  # noqa: BLE001 - fall back to heuristics.
        log.warning("Hosted vision validation failed: %s", exc)
        return None


def _heuristic(image_path: str) -> dict:
    """Local, dependency-light validation using Pillow and basic file checks."""
    try:
        size = os.path.getsize(image_path)
    except OSError:
        return _unavailable("Uploaded file could not be read.")

    if size < 1024:
        return {"valid": False, "method": "heuristic", "message": "File is too small to be a document.",
                "details": {"size_bytes": size}}
    if size > current_app.config.get("MAX_CONTENT_LENGTH", 8 * 1024 * 1024):
        return {"valid": False, "method": "heuristic", "message": "File is too large.",
                "details": {"size_bytes": size}}

    # PDFs are treated as documents by extension (Pillow cannot open them directly).
    if image_path.lower().endswith(".pdf"):
        return {"valid": True, "method": "heuristic", "message": "Accepted as a PDF document.",
                "details": {"type": "pdf", "size_bytes": size}}

    try:
        from PIL import Image

        with Image.open(image_path) as img:
            width, height = img.size
            img.verify()  # confirm it is not corrupt
    except Exception as exc:  # noqa: BLE001
        return {"valid": False, "method": "heuristic",
                "message": "The file is not a readable image.", "details": {"error": str(exc)}}

    if width < 100 or height < 100:
        return {"valid": False, "method": "heuristic",
                "message": "Image resolution is too low to be a document.",
                "details": {"width": width, "height": height}}

    aspect = width / height if height else 0
    if not (0.2 <= aspect <= 5.0):
        return {"valid": False, "method": "heuristic",
                "message": "Image shape does not look like a document.",
                "details": {"aspect_ratio": round(aspect, 2)}}

    return {"valid": True, "method": "heuristic",
            "message": "Looks like a document (heuristic check passed).",
            "details": {"width": width, "height": height, "size_bytes": size}}


def _unavailable(reason: str) -> dict:
    return {"valid": None, "method": "unavailable",
            "message": f"AI validation unavailable — manual confirmation required. ({reason})",
            "details": {}}
