"""MedCloud application entry point.

Run locally with:
    python run.py

This creates the Flask application via the application factory (app/__init__.py)
and starts the development server. Production/Docker uses gunicorn against
`app:create_app()` (see Dockerfile).
"""
from app import create_app
from app.config import Config

config = Config()

# The module-level `app` object is what gunicorn / Render import (`run:app`).
app = create_app(config)

if __name__ == "__main__":
    # host=0.0.0.0 so the server is reachable from inside a Docker container.
    app.run(host="0.0.0.0", port=app.config.get("PORT", 5000), debug=app.config.get("DEBUG", False))
