"""Main controller — landing page, role dashboard routing, and health check."""
from flask import Blueprint, abort, current_app, jsonify, redirect, send_from_directory, url_for
from flask_login import current_user, login_required

from app.extensions import csrf
from app.services import database_service

main_bp = Blueprint("main", __name__)


@main_bp.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    """Serve uploaded files (patient photos, prescription scans) to logged-in staff."""
    return send_from_directory(current_app.config["UPLOAD_DIR"], filename)


@main_bp.route("/prescriptions/file/<path:filename>")
@login_required
def prescription_pdf_file(filename):
    """Serve a locally generated prescription PDF (used when Cloudinary is not configured).

    Lives on the shared `main` blueprint (not the doctor one) because doctors AND
    pharmacists both need to open prescription PDFs.
    """
    return send_from_directory(current_app.config["GENERATED_PDF_DIR"], filename, as_attachment=False)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Send each user to the dashboard that matches their role."""
    routes = {
        "admin": "admin.dashboard",
        "doctor": "doctor.dashboard",
        "pharmacist": "pharmacist.dashboard",
    }
    endpoint = routes.get(current_user.role)
    if not endpoint:
        abort(403)
    return redirect(url_for(endpoint))


@main_bp.route("/health")
@csrf.exempt
def health():
    """Lightweight health/status endpoint (useful for Docker/Render probes)."""
    return jsonify({"status": "ok", "database": database_service.get_mode()}), 200
