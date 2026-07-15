"""Report which cloud services are live vs running in fallback mode.

Used by the base template's status panel and the DEFENSE_GUIDE so it is always
obvious (to us and to the examiner) which integrations are using real credentials
and which are gracefully degraded to a local/fallback mode.

Accepts Flask's `app.config` mapping (dict-like), so values are read with `.get()`.
"""
from app.services import database_service


def service_status_summary(config) -> list:
    """Return a list of {name, detail, live} describing each external service."""
    return [
        {
            "name": "Database",
            "detail": database_service.get_mode(),
            "live": not database_service.is_demo_mode(),
        },
        {
            "name": "PDF storage",
            "detail": "Cloudinary" if _cloudinary_ready(config) else "Local generated_pdfs/ fallback",
            "live": _cloudinary_ready(config),
        },
        {
            "name": "Diagnosis search",
            "detail": "Tavily" if config.get("TAVILY_API_KEY") else "OpenFDA / message fallback",
            "live": bool(config.get("TAVILY_API_KEY")),
        },
        {
            "name": "Clinical trials",
            "detail": "ClinicalTrials.gov (public API)",
            "live": True,
        },
        {
            "name": "OCR",
            "detail": "Cloud OCR" if config.get("OCR_API_URL") else "Tesseract / manual fallback",
            "live": bool(config.get("OCR_API_URL")),
        },
        {
            "name": "AI document validator",
            "detail": "Hosted vision model" if config.get("VISION_API_URL") else "Heuristic fallback",
            "live": bool(config.get("VISION_API_URL")),
        },
    ]


def _cloudinary_ready(config) -> bool:
    return bool(
        config.get("CLOUDINARY_CLOUD_NAME")
        and config.get("CLOUDINARY_API_KEY")
        and config.get("CLOUDINARY_API_SECRET")
    )
