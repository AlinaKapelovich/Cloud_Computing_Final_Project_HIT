"""Prescription model — a prescription with embedded medication items.

Status values : open | dispensed | cancelled
Source values : digital | handwritten_upload

The PDF may be stored on Cloudinary (pdf_url) and/or locally (pdf_path); pdf_storage
records which backend actually holds it.
"""
from app.services.database_service import get_collection
from app.utils.date_utils import now_utc
from app.utils.db_utils import serialize_id, to_object_id

STATUS_OPEN = "open"
STATUS_DISPENSED = "dispensed"
STATUS_CANCELLED = "cancelled"

SOURCE_DIGITAL = "digital"
SOURCE_UPLOAD = "handwritten_upload"


class Prescription:
    COLLECTION = "prescriptions"

    @staticmethod
    def _collection():
        return get_collection(Prescription.COLLECTION)

    @classmethod
    def create(cls, *, patient, doctor, diagnosis, items, visit_id=None,
               source=SOURCE_DIGITAL, ocr_text=None, ai_validation=None):
        document = {
            "patient_id": patient.get("id"),
            "patient_national_id": patient.get("national_id"),
            "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip(),
            "doctor_id": getattr(doctor, "id", None),
            "doctor_name": getattr(doctor, "full_name", "Uploaded"),
            "visit_id": visit_id,
            "diagnosis": (diagnosis or "").strip(),
            "items": items or [],
            "status": STATUS_OPEN,
            "source": source,
            "pdf_path": None,
            "pdf_url": None,
            "pdf_storage": None,
            "ocr_text": ocr_text,
            "ai_document_validation_result": ai_validation,
            "created_at": now_utc(),
            "dispensed_at": None,
            "dispensed_by": None,
        }
        result = cls._collection().insert_one(document)
        document["_id"] = result.inserted_id
        return serialize_id(document)

    @classmethod
    def set_pdf(cls, prescription_id, pdf_path=None, pdf_url=None, pdf_storage=None):
        oid = to_object_id(prescription_id)
        if oid is None:
            return False
        update = {"pdf_path": pdf_path, "pdf_url": pdf_url, "pdf_storage": pdf_storage}
        return cls._collection().update_one({"_id": oid}, {"$set": update}).matched_count > 0

    @classmethod
    def dispense(cls, prescription_id, pharmacist):
        oid = to_object_id(prescription_id)
        if oid is None:
            return False
        update = {
            "status": STATUS_DISPENSED,
            "dispensed_at": now_utc(),
            "dispensed_by": getattr(pharmacist, "full_name", "pharmacist"),
        }
        return cls._collection().update_one(
            {"_id": oid, "status": STATUS_OPEN}, {"$set": update}
        ).modified_count > 0

    @classmethod
    def get_by_id(cls, prescription_id):
        oid = to_object_id(prescription_id)
        if oid is None:
            return None
        return serialize_id(cls._collection().find_one({"_id": oid}))

    @classmethod
    def list_by_doctor(cls, doctor_id):
        docs = cls._collection().find({"doctor_id": doctor_id}).sort("created_at", -1)
        return [serialize_id(doc) for doc in docs]

    @classmethod
    def list_by_patient(cls, national_id, status=None):
        query = {"patient_national_id": national_id}
        if status:
            query["status"] = status
        docs = cls._collection().find(query).sort("created_at", -1)
        return [serialize_id(doc) for doc in docs]

    @classmethod
    def counts_by_status(cls):
        col = cls._collection()
        return {
            "open": col.count_documents({"status": STATUS_OPEN}),
            "dispensed": col.count_documents({"status": STATUS_DISPENSED}),
            "cancelled": col.count_documents({"status": STATUS_CANCELLED}),
        }
