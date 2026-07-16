"""MedCloud application factory.

This is the composition root of the app. It follows the Flask "application factory"
pattern: `create_app()` builds and configures the Flask application, wires up the
extensions, the database, the blueprints (Controllers) and the error handlers.

MVC mapping for this project:
  * Controllers  -> app/controllers/*  (Flask blueprints/routes)
  * Views        -> app/templates/*    (Jinja2 templates)
  * Models       -> app/models/*       (data entities + MongoDB access)
  * Services     -> app/services/*      (business logic + external cloud APIs)
"""
import logging

from flask import Flask, render_template

from app.config import Config
from app.extensions import csrf, login_manager
from app.services import database_service


def create_app(config_object: type = Config) -> Flask:
    """Build and return a fully configured Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    logging.basicConfig(level=logging.INFO)
    _warn_on_insecure_secret_key(app)

    _ensure_runtime_directories(app)
    database_service.init_db(config_object)

    # Seed demo accounts (in-memory demo mode by default; real databases require
    # SEED_DEMO_USERS=true to opt in — see app/services/bootstrap.py).
    from app.services.bootstrap import ensure_demo_users

    ensure_demo_users(config_object)

    # Initialise extensions.
    login_manager.init_app(app)
    csrf.init_app(app)
    _register_login_manager()

    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)

    return app


def _warn_on_insecure_secret_key(app: Flask) -> None:
    """Loudly warn if the app is running outside debug with the placeholder SECRET_KEY.

    Sessions and CSRF tokens are signed with this key, so a real deployment must set it
    (Render generates one automatically via render.yaml).
    """
    if app.config.get("SECRET_KEY") == "dev-insecure-secret-change-me" and not app.config.get("DEBUG"):
        logging.getLogger(__name__).warning(
            "SECRET_KEY is the insecure default. Set the SECRET_KEY environment variable "
            "before deploying — sessions and CSRF tokens depend on it."
        )


def _ensure_runtime_directories(app: Flask) -> None:
    """Create the folders used for uploads and generated PDFs if they don't exist."""
    for directory in (app.config["UPLOAD_DIR"], app.config["GENERATED_PDF_DIR"]):
        directory.mkdir(parents=True, exist_ok=True)


def _register_login_manager() -> None:
    """Connect Flask-Login to our User model."""
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):  # noqa: WPS430 - closure required by Flask-Login API.
        return User.get_by_id(user_id)


def _register_blueprints(app: Flask) -> None:
    """Register every controller blueprint."""
    from app.controllers.main_controller import main_bp
    from app.controllers.auth_controller import auth_bp
    from app.controllers.admin_controller import admin_bp
    from app.controllers.doctor_controller import doctor_bp
    from app.controllers.pharmacist_controller import pharmacist_bp
    from app.controllers.api_controller import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(pharmacist_bp)
    app.register_blueprint(api_bp)


def _register_error_handlers(app: Flask) -> None:
    """Friendly, styled error pages instead of raw stack traces."""
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(413)
    def payload_too_large(_error):
        """Upload exceeded MAX_CONTENT_LENGTH — show a styled page, not Werkzeug's default."""
        limit_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return render_template("errors/413.html", limit_mb=limit_mb), 413

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        """Expired/missing CSRF token (e.g. the session timed out on an open form)."""
        return render_template("errors/csrf.html", reason=error.description), 400

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("errors/500.html"), 500


def _register_context_processors(app: Flask) -> None:
    """Inject values that every template can use (branding, DB mode, service status)."""
    from app.utils.date_utils import now_utc
    from app.utils.service_status import service_status_summary

    @app.context_processor
    def inject_globals():
        return {
            "APP_NAME": "MedCloud",
            "APP_TAGLINE": "Cloud Prescription Management",
            "current_year": now_utc().year,
            "db_mode": database_service.get_mode(),
            "service_status": service_status_summary(app.config),
            # Set of registered endpoint names, so templates can conditionally show
            # navigation links only for features that are actually implemented.
            "endpoints": set(app.view_functions.keys()),
        }
