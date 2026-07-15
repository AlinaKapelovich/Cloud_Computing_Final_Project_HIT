"""Application configuration.

All configuration is read from environment variables (loaded from a local .env file
in development via python-dotenv). Secrets are NEVER hardcoded here — this file only
reads values and provides safe defaults that keep the app runnable in demo mode.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present (development convenience). In production the platform
# (Docker / Render) injects real environment variables instead.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _flag(name: str, default: str = "0") -> bool:
    """Interpret an environment variable as a boolean flag."""
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Central configuration object consumed by the Flask application factory."""

    # --- Flask core ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-change-me")
    DEBUG = _flag("FLASK_DEBUG", "1")
    PORT = int(os.getenv("PORT", "5000"))

    # --- Filesystem paths ---
    BASE_DIR = BASE_DIR
    UPLOAD_DIR = BASE_DIR / "uploads"
    GENERATED_PDF_DIR = BASE_DIR / "generated_pdfs"
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB cap on uploads
    ALLOWED_UPLOAD_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "pdf"}

    # --- Database (MongoDB Atlas, with in-memory fallback) ---
    MONGO_URI = os.getenv("MONGO_URI", "").strip()
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "medcloud").strip() or "medcloud"

    # --- Cloud storage (Cloudinary) ---
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "").strip()
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "").strip()

    # --- Diagnosis search (Tavily) ---
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()

    # --- OCR (cloud-first, then Tesseract, then manual) ---
    OCR_API_URL = os.getenv("OCR_API_URL", "").strip()
    OCR_API_KEY = os.getenv("OCR_API_KEY", "").strip()

    # --- AI document validator (hosted vision, then heuristics) ---
    VISION_API_URL = os.getenv("VISION_API_URL", "").strip()
    VISION_API_KEY = os.getenv("VISION_API_KEY", "").strip()

    # --- Public medical APIs (no key required) ---
    CLINICAL_TRIALS_BASE_URL = os.getenv(
        "CLINICAL_TRIALS_BASE_URL", "https://clinicaltrials.gov/api/v2"
    ).strip()
    OPENFDA_BASE_URL = os.getenv("OPENFDA_BASE_URL", "https://api.fda.gov").strip()

    # --- Bonus future extensions (stubs only, disabled by default) ---
    KAFKA_ENABLED = _flag("KAFKA_ENABLED", "0")
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "").strip()
    OLLAMA_ENABLED = _flag("OLLAMA_ENABLED", "0")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
