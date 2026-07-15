"""File upload helpers — safe saving of user-uploaded files (photos, scans)."""
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in current_app.config["ALLOWED_UPLOAD_EXTENSIONS"]


def save_upload(file_storage, subdir: str = "") -> str | None:
    """Save an uploaded file under uploads/<subdir> with a random name.

    Returns the stored path relative to the uploads directory, or None if there was
    no valid file. Randomising the name avoids collisions and path-traversal issues.
    """
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None
    if not allowed_file(file_storage.filename):
        return None

    ext = secure_filename(file_storage.filename).rsplit(".", 1)[-1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    dest_dir = Path(current_app.config["UPLOAD_DIR"]) / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    file_storage.save(str(dest_dir / stored_name))

    return f"{subdir}/{stored_name}" if subdir else stored_name


def absolute_upload_path(relative_path: str) -> Path:
    """Resolve a stored relative upload path to an absolute filesystem path."""
    return Path(current_app.config["UPLOAD_DIR"]) / relative_path
