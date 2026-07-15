"""User model — application accounts and role-based identity.

Model responsibility: represent a user document and provide the persistence logic
for creating and looking up users in the `users` collection. Passwords are stored
only as salted hashes (Werkzeug), never in plain text.

Roles: "admin", "doctor", "pharmacist".
"""
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.services.database_service import get_collection
from app.utils.date_utils import now_utc
from app.utils.db_utils import to_object_id

ROLES = ("admin", "doctor", "pharmacist")


class User(UserMixin):
    """A logged-in identity backed by a MongoDB `users` document."""

    def __init__(self, document: dict):
        self._doc = document
        self.id = str(document.get("_id"))
        self.full_name = document.get("full_name", "")
        self.email = document.get("email", "")
        self.role = document.get("role", "")
        self.password_hash = document.get("password_hash", "")
        self.created_at = document.get("created_at")

    # Flask-Login uses get_id(); UserMixin returns self.id by default.
    def get_id(self):
        return self.id

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_doctor(self) -> bool:
        return self.role == "doctor"

    @property
    def is_pharmacist(self) -> bool:
        return self.role == "pharmacist"

    def check_password(self, password: str) -> bool:
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    # ----- Lookups / persistence -----
    @staticmethod
    def _collection():
        return get_collection("users")

    @classmethod
    def get_by_id(cls, user_id):
        oid = to_object_id(user_id)
        if oid is None:
            return None
        doc = cls._collection().find_one({"_id": oid})
        return cls(doc) if doc else None

    @classmethod
    def get_by_email(cls, email: str):
        if not email:
            return None
        doc = cls._collection().find_one({"email": email.strip().lower()})
        return cls(doc) if doc else None

    @classmethod
    def create(cls, full_name: str, email: str, password: str, role: str):
        """Create a new user with a hashed password. Returns the User."""
        if role not in ROLES:
            raise ValueError(f"Invalid role: {role}")
        document = {
            "full_name": full_name.strip(),
            "email": email.strip().lower(),
            "password_hash": generate_password_hash(password),
            "role": role,
            "created_at": now_utc(),
        }
        result = cls._collection().insert_one(document)
        document["_id"] = result.inserted_id
        return cls(document)

    @classmethod
    def count(cls) -> int:
        return cls._collection().count_documents({})
