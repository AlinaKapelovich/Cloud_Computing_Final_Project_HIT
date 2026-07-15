"""Standalone seed script for the demo users.

Use this against a real MongoDB Atlas database (set MONGO_URI first):

    python -m scripts.seed_users

In demo mode the app already seeds these users automatically on startup, so this
script is mainly for provisioning a persistent Atlas database before a defense.
The demo password comes from DEMO_PASSWORD (default "demo1234") — never a real secret.
"""
from app import create_app
from app.services.bootstrap import DEMO_USERS, ensure_demo_users
from app.models.user import User


def main() -> None:
    # create_app() initialises the database and already calls ensure_demo_users().
    create_app()
    ensure_demo_users()  # idempotent — safe to call again.
    print("Demo users present:")
    for _name, email, role in DEMO_USERS:
        user = User.get_by_email(email)
        print(f"  [{'ok' if user else 'MISSING'}] {email} ({role})")


if __name__ == "__main__":
    main()
