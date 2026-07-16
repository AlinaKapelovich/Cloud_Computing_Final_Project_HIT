"""bootstrap.py — demo user seeding policy.

Covers the exact scenario docker-compose.yml now relies on: a real MONGO_URI configured
(so the database is NOT in demo/in-memory mode) plus an explicit SEED_DEMO_USERS=true,
which must still seed all three role accounts. Without this fix, a fresh Docker database
had no users at all and the login page was unusable — see docker-compose.yml.

No real MongoDB is required here: `database_service.is_demo_mode()` is monkeypatched to
simulate "a real, connected database" without needing a reachable MongoDB instance.
"""
from app.models.user import User
from app.services import bootstrap, database_service
from app.services.database_service import get_collection


class _FakeConfig:
    def __init__(self, seed_demo_users, demo_password="demo1234"):
        self.SEED_DEMO_USERS = seed_demo_users
        self.DEMO_PASSWORD = demo_password


def _clear_users():
    """The `app` fixture's own create_app() already auto-seeds 3 demo users in the
    default (in-memory demo mode) case — clear them so each test starts from a known,
    genuinely empty state, matching a truly fresh database."""
    get_collection("users").delete_many({})


def test_explicit_seed_true_seeds_all_three_roles_even_on_a_real_database(app, monkeypatch):
    """The docker-compose.yml scenario: MONGO_URI set (real DB) + SEED_DEMO_USERS=true."""
    monkeypatch.setattr(database_service, "is_demo_mode", lambda: False)
    _clear_users()
    assert User.count() == 0

    bootstrap.ensure_demo_users(_FakeConfig(seed_demo_users=True))

    assert User.count() == 3
    for _full_name, email, role in bootstrap.DEMO_USERS:
        user = User.get_by_email(email)
        assert user is not None, f"{email} was not seeded"
        assert user.role == role
        assert user.check_password("demo1234")


def test_admin_doctor_pharmacist_all_present_after_seeding(app, monkeypatch):
    """Explicit check that all three required roles exist, not just a user count."""
    monkeypatch.setattr(database_service, "is_demo_mode", lambda: False)
    _clear_users()
    bootstrap.ensure_demo_users(_FakeConfig(seed_demo_users=True))

    roles = {User.get_by_email(email).role for _n, email, _r in bootstrap.DEMO_USERS}
    assert roles == {"admin", "doctor", "pharmacist"}


def test_no_explicit_flag_does_not_seed_on_a_real_database(app, monkeypatch):
    """Without SEED_DEMO_USERS, a real (non-demo) database must NOT be silently seeded."""
    monkeypatch.setattr(database_service, "is_demo_mode", lambda: False)
    _clear_users()

    bootstrap.ensure_demo_users(_FakeConfig(seed_demo_users=None))

    assert User.count() == 0


def test_no_explicit_flag_still_seeds_in_demo_mode(app, monkeypatch):
    """The default in-memory demo experience (no MONGO_URI) keeps auto-seeding."""
    monkeypatch.setattr(database_service, "is_demo_mode", lambda: True)
    _clear_users()

    bootstrap.ensure_demo_users(_FakeConfig(seed_demo_users=None))

    assert User.count() == 3


def test_explicit_seed_false_blocks_seeding_even_in_demo_mode(app, monkeypatch):
    monkeypatch.setattr(database_service, "is_demo_mode", lambda: True)
    _clear_users()

    bootstrap.ensure_demo_users(_FakeConfig(seed_demo_users=False))

    assert User.count() == 0


def test_seeding_is_idempotent(app, monkeypatch):
    """Re-running ensure_demo_users (e.g. container restart) must not duplicate users."""
    monkeypatch.setattr(database_service, "is_demo_mode", lambda: False)
    _clear_users()
    config = _FakeConfig(seed_demo_users=True)

    bootstrap.ensure_demo_users(config)
    bootstrap.ensure_demo_users(config)

    assert User.count() == 3
