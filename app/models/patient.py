"""Patient model — patient records managed by the Admin.

Stores the birth date (not a frozen age) plus demographic and contact details.
The `national_id` is the human-facing unique key used by doctors and pharmacists
to look a patient up.
"""
from app.services.database_service import get_collection
from app.utils.date_utils import calculate_age, now_utc, parse_date
from app.utils.db_utils import serialize_id, to_object_id

GENDERS = ("female", "male", "other")


class Patient:
    COLLECTION = "patients"

    @staticmethod
    def _collection():
        return get_collection(Patient.COLLECTION)

    @staticmethod
    def _decorate(document):
        """Attach derived fields (id string, calculated age) for the templates."""
        if not document:
            return None
        document = serialize_id(document)
        document["age"] = calculate_age(document.get("birth_date"))
        return document

    @staticmethod
    def build_document(data: dict) -> dict:
        """Normalise raw form input into a patient document (no persistence)."""
        birth = parse_date(data.get("birth_date"))
        return {
            "national_id": (data.get("national_id") or "").strip(),
            "first_name": (data.get("first_name") or "").strip(),
            "last_name": (data.get("last_name") or "").strip(),
            "gender": (data.get("gender") or "").strip().lower(),
            "pregnancy_status": bool(data.get("pregnancy_status")),
            "lactation_status": bool(data.get("lactation_status")),
            "birth_date": birth.isoformat() if birth else None,
            "photo": (data.get("photo") or "").strip(),
            "email": (data.get("email") or "").strip().lower(),
            "phone": (data.get("phone") or "").strip(),
        }

    @classmethod
    def create(cls, data: dict):
        document = cls.build_document(data)
        document["created_at"] = now_utc()
        document["updated_at"] = document["created_at"]
        result = cls._collection().insert_one(document)
        document["_id"] = result.inserted_id
        return cls._decorate(document)

    @classmethod
    def update(cls, patient_id, data: dict) -> bool:
        oid = to_object_id(patient_id)
        if oid is None:
            return False
        update_doc = cls.build_document(data)
        update_doc["updated_at"] = now_utc()
        result = cls._collection().update_one({"_id": oid}, {"$set": update_doc})
        return result.matched_count > 0

    @classmethod
    def get_by_id(cls, patient_id):
        oid = to_object_id(patient_id)
        if oid is None:
            return None
        return cls._decorate(cls._collection().find_one({"_id": oid}))

    @classmethod
    def get_by_national_id(cls, national_id: str):
        if not national_id:
            return None
        return cls._decorate(cls._collection().find_one({"national_id": national_id.strip()}))

    @classmethod
    def list_all(cls):
        docs = cls._collection().find().sort("created_at", -1)
        return [cls._decorate(doc) for doc in docs]

    @classmethod
    def count(cls) -> int:
        return cls._collection().count_documents({})

    @classmethod
    def national_id_exists(cls, national_id: str, exclude_id=None) -> bool:
        query = {"national_id": (national_id or "").strip()}
        doc = cls._collection().find_one(query)
        if not doc:
            return False
        if exclude_id and str(doc.get("_id")) == str(exclude_id):
            return False
        return True
