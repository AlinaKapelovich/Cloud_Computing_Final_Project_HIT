"""Report the configuration/verification status of each external cloud service.

Status values (never conflated with each other):
  - "Fallback"   — no credentials/config present; the app uses its documented local
                   fallback path for this service.
  - "Configured" — credentials/config ARE present, so the app will attempt a real call
                   at runtime. This is NOT a claim that a live call has ever succeeded —
                   a keyless public API (ClinicalTrials.gov) is also only "Configured",
                   never "live" merely because it's reachable in principle.
  - "Verified"   — a human has manually confirmed a real, successful live call for this
                   service and recorded it (with date + result) in
                   docs/LIVE_VERIFICATION.md, then added the service's key to the
                   LIVE_VERIFIED_SERVICES env var. This status is never set
                   automatically by application code, and pytest never sets that env
                   var, so a mocked test can never make a service appear "Verified".

Used by the base template's footer status panel and the defense guide so it is always
obvious which integrations are real vs. fallback vs. actually proven to work live.
Accepts Flask's `app.config` mapping (dict-like), so values are read with `.get()`.
"""
from app.services import database_service

# Service keys recognised in LIVE_VERIFIED_SERVICES (comma-separated, case-insensitive).
KEY_DATABASE = "mongodb"
KEY_PDF_STORAGE = "cloudinary"
KEY_DIAGNOSIS_SEARCH = "tavily"
KEY_CLINICAL_TRIALS = "clinicaltrials"
KEY_OCR = "ocr"
KEY_AI_VALIDATOR = "vision"


def _verified_keys(config) -> set:
    raw = config.get("LIVE_VERIFIED_SERVICES", "") or ""
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def _status(configured: bool, verified: bool) -> str:
    if verified:
        return "Verified"
    return "Configured" if configured else "Fallback"


def service_status_summary(config) -> list:
    """Return a list of {name, detail, status} describing each external service."""
    verified = _verified_keys(config)

    db_configured = not database_service.is_demo_mode()
    cloudinary_configured = _cloudinary_ready(config)
    tavily_configured = bool(config.get("TAVILY_API_KEY"))
    # OCR is "configured" if EITHER the Hugging Face token or the generic cloud OCR
    # endpoint is set — previously this only checked OCR_API_URL and silently ignored
    # HUGGINGFACE_API_TOKEN, which is the primary, concretely-implemented provider.
    ocr_configured = bool(config.get("HUGGINGFACE_API_TOKEN") or config.get("OCR_API_URL"))
    vision_configured = bool(config.get("VISION_API_URL"))

    if config.get("HUGGINGFACE_API_TOKEN"):
        ocr_detail = f"Hugging Face ({config.get('HUGGINGFACE_OCR_MODEL') or 'trocr-base-handwritten'})"
    elif config.get("OCR_API_URL"):
        ocr_detail = "Generic cloud OCR"
    else:
        ocr_detail = "Tesseract / manual fallback"

    return [
        {
            "name": "Database",
            "detail": database_service.get_mode(),
            "status": _status(db_configured, db_configured and KEY_DATABASE in verified),
        },
        {
            "name": "PDF storage",
            "detail": "Cloudinary" if cloudinary_configured else "Local generated_pdfs/ fallback",
            "status": _status(cloudinary_configured, cloudinary_configured and KEY_PDF_STORAGE in verified),
        },
        {
            "name": "Diagnosis search",
            "detail": "Tavily" if tavily_configured else "OpenFDA / message fallback",
            "status": _status(tavily_configured, tavily_configured and KEY_DIAGNOSIS_SEARCH in verified),
        },
        {
            "name": "Clinical trials",
            "detail": "ClinicalTrials.gov (public API, keyless)",
            # Reachable without a key, but "reachable" is not "verified" — being public
            # never earns this a "Verified" status on its own, only "Configured".
            "status": _status(True, KEY_CLINICAL_TRIALS in verified),
        },
        {
            "name": "OCR",
            "detail": ocr_detail,
            "status": _status(ocr_configured, ocr_configured and KEY_OCR in verified),
        },
        {
            "name": "AI document validator",
            "detail": "Hosted vision model" if vision_configured else "Heuristic fallback",
            "status": _status(vision_configured, vision_configured and KEY_AI_VALIDATOR in verified),
        },
    ]


def _cloudinary_ready(config) -> bool:
    return bool(
        config.get("CLOUDINARY_CLOUD_NAME")
        and config.get("CLOUDINARY_API_KEY")
        and config.get("CLOUDINARY_API_SECRET")
    )
