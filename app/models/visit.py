"""Visit model — a clinical encounter recorded by a doctor for a patient.

Stores the complaints and diagnosis captured during the visit. A prescription can
later be linked to a visit.
"""
from app.services.database_service import get_collection
from app.utils.date_utils import now_utc
from app.utils.db_utils import serialize_id, to_object_id


class Visit:
    COLLECTION = "visits"

    @staticmethod
    def _collection():
        return get_collection(Visit.COLLECTION)

    @classmethod
    def create(cls, patient: dict, doctor, complaints: str, diagnosis: str):
        document = {
            "patient_id": patient.get("id"),
            "patient_national_id": patient.get("national_id"),
            "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip(),
            "doctor_id": doctor.id,
            "doctor_name": doctor.full_name,
            "complaints": (complaints or "").strip(),
            "diagnosis": (diagnosis or "").strip(),
            "created_at": now_utc(),
        }
        result = cls._collection().insert_one(document)
        document["_id"] = result.inserted_id
        return serialize_id(document)

    @classmethod
    def get_by_id(cls, visit_id):
        oid = to_object_id(visit_id)
        if oid is None:
            return None
        return serialize_id(cls._collection().find_one({"_id": oid}))
