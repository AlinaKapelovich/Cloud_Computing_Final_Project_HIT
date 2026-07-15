"""ServiceQueryLog model — audit log of external consultation queries.

Every call to the search / clinical-trials / side-effects services is logged so we
can show a history and demonstrate how the app consumes cloud services. Stored in the
`service_query_logs` collection.
"""
from app.services.database_service import get_collection
from app.utils.date_utils import now_utc
from app.utils.db_utils import serialize_id


class ServiceQueryLog:
    COLLECTION = "service_query_logs"

    @staticmethod
    def _collection():
        return get_collection(ServiceQueryLog.COLLECTION)

    @classmethod
    def log(cls, *, service: str, query: str, source: str, result_count: int, user=None):
        document = {
            "service": service,          # e.g. "diagnosis_search", "clinical_trials"
            "query": (query or "").strip(),
            "source": source,            # which provider actually answered (Tavily/OpenFDA/...)
            "result_count": int(result_count or 0),
            "user_id": getattr(user, "id", None),
            "user_name": getattr(user, "full_name", None),
            "created_at": now_utc(),
        }
        try:
            cls._collection().insert_one(document)
        except Exception:  # noqa: BLE001 - logging must never break a consultation.
            pass

    @classmethod
    def recent(cls, limit: int = 20):
        docs = cls._collection().find().sort("created_at", -1).limit(limit)
        return [serialize_id(doc) for doc in docs]
