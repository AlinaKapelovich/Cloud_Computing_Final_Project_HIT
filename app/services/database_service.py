"""database_service.py — Data layer access to MongoDB.

Responsibility (Service / data-access): provide the rest of the app with a MongoDB
database handle, hiding whether we are connected to the real cloud database
(MongoDB Atlas) or the in-memory demo database (mongomock).

Cloud concept demonstrated: MongoDB is a NoSQL, document database. A `Database`
holds `Collections`, and each `Collection` holds JSON-like `Documents`.

Fallback behaviour: if MONGO_URI is not configured, or the cloud database cannot be
reached, we automatically fall back to mongomock (an in-memory Mongo) so the whole
application still runs and can be demonstrated with zero cloud credentials.
"""
import logging

log = logging.getLogger(__name__)

# Module-level singleton state, initialised once by init_db() from the app factory.
_state = {"db": None, "client": None, "mode": "uninitialized"}

# Human-readable labels shown in the UI so it is obvious which mode is active.
MODE_ATLAS = "MongoDB Atlas (cloud)"
MODE_DEMO = "In-memory demo (mongomock)"


def init_db(config):
    """Connect to MongoDB Atlas if configured, otherwise start the in-memory fallback."""
    uri = getattr(config, "MONGO_URI", "")
    db_name = getattr(config, "MONGO_DB_NAME", "medcloud")

    if uri:
        try:
            from pymongo import MongoClient

            client = MongoClient(uri, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
            client.admin.command("ping")  # Force a real connection check.
            _state.update(client=client, db=client[db_name], mode=MODE_ATLAS)
            log.info("Connected to MongoDB Atlas database '%s'.", db_name)
            _ensure_indexes()
            return _state["db"]
        except Exception as exc:  # noqa: BLE001 - any failure should degrade gracefully.
            log.warning("MongoDB Atlas unavailable (%s). Falling back to in-memory demo DB.", exc)

    # Fallback: in-memory database. Nothing persists across restarts, but the app works.
    import mongomock

    client = mongomock.MongoClient()
    _state.update(client=client, db=client[db_name], mode=MODE_DEMO)
    log.info("Using in-memory demo database (mongomock). Set MONGO_URI for persistent storage.")
    _ensure_indexes()
    return _state["db"]


def _ensure_indexes():
    """Create the indexes that enforce our core uniqueness rules."""
    db = _state["db"]
    if db is None:
        return
    try:
        db.users.create_index("email", unique=True)
        db.patients.create_index("national_id", unique=True)
        db.prescriptions.create_index("patient_national_id")
        db.prescriptions.create_index("status")
        db.visits.create_index("patient_national_id")
        db.service_query_logs.create_index("created_at")
    except Exception as exc:  # noqa: BLE001 - index creation must never crash startup.
        log.warning("Could not create one or more indexes: %s", exc)


def get_db():
    """Return the active database handle (Atlas or demo)."""
    if _state["db"] is None:
        raise RuntimeError("Database not initialised. Call init_db() in the app factory first.")
    return _state["db"]


def get_collection(name: str):
    """Convenience accessor for a single collection."""
    return get_db()[name]


def get_mode() -> str:
    """Return the human-readable active database mode (for the UI/status)."""
    return _state["mode"]


def is_demo_mode() -> bool:
    """True when running on the in-memory fallback rather than real Atlas."""
    return _state["mode"] != MODE_ATLAS
