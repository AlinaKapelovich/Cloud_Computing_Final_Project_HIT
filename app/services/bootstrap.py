"""bootstrap.py — first-run seeding of demo users.

Seeding policy:
  - If SEED_DEMO_USERS is explicitly set (true/false), that decision is honored as-is —
    this lets a real deployment opt in deliberately (e.g. an academic demo on Render).
  - If SEED_DEMO_USERS is not set, demo users are seeded only when the app is running on
    the in-memory demo database (no MONGO_URI configured). A real, persistent database
    (MongoDB Atlas) is never silently populated with known demo1234-password accounts.

This keeps the "runs with zero credentials" experience for local development and tests
while refusing to quietly create demo accounts in a real production database.
"""
import logging

from app.models.user import User
from app.services import database_service

log = logging.getLogger(__name__)

DEMO_USERS = [
    ("System Administrator", "admin@example.com", "admin"),
    ("Dr. Dana Cohen", "doctor@example.com", "doctor"),
    ("Pharmacist Noa Levi", "pharmacist@example.com", "pharmacist"),
]


def ensure_demo_users(config=None) -> None:
    """Create the demo accounts if seeding is enabled and none exist yet. Non-fatal."""
    try:
        explicit = None if config is None else config.SEED_DEMO_USERS
        should_seed = explicit if explicit is not None else database_service.is_demo_mode()

        if not should_seed:
            log.info(
                "Demo user seeding skipped: a real database is configured and "
                "SEED_DEMO_USERS was not explicitly enabled."
            )
            return
        if User.count() > 0:
            return

        password = None if config is None else config.DEMO_PASSWORD
        password = password or "demo1234"
        for full_name, email, role in DEMO_USERS:
            User.create(full_name, email, password, role)
        log.info("Seeded %d demo users (password from DEMO_PASSWORD, default 'demo1234').", len(DEMO_USERS))
    except Exception as exc:  # noqa: BLE001 - seeding must never crash startup.
        log.warning("Could not seed demo users: %s", exc)
