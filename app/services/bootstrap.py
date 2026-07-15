"""bootstrap.py — first-run seeding of demo users.

In demo mode the database is in-memory, so we seed the three role accounts on
startup whenever the users collection is empty. This guarantees the app is usable
immediately (and makes the login page's demo credentials real) without committing
any secret: the demo password comes from DEMO_PASSWORD (default "demo1234").
"""
import logging
import os

from app.models.user import User

log = logging.getLogger(__name__)

DEMO_USERS = [
    ("System Administrator", "admin@example.com", "admin"),
    ("Dr. Dana Cohen", "doctor@example.com", "doctor"),
    ("Pharmacist Noa Levi", "pharmacist@example.com", "pharmacist"),
]


def ensure_demo_users() -> None:
    """Create the demo accounts if no users exist yet. Idempotent and non-fatal."""
    try:
        if User.count() > 0:
            return
        password = os.getenv("DEMO_PASSWORD", "demo1234")
        for full_name, email, role in DEMO_USERS:
            User.create(full_name, email, password, role)
        log.info("Seeded %d demo users (password from DEMO_PASSWORD, default 'demo1234').", len(DEMO_USERS))
    except Exception as exc:  # noqa: BLE001 - seeding must never crash startup.
        log.warning("Could not seed demo users: %s", exc)
