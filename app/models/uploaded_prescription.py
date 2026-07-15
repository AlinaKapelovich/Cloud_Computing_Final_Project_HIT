"""UploadedPrescription model — a handwritten prescription uploaded by a pharmacist.

Holds the uploaded image, the AI document-validation result, and the OCR text
(reviewed/edited by the pharmacist before dispensing).

Status : open | dispensed
Source : handwritten_upload
"""
from app.services.database_service import get_collection
from app.utils.date_utils import now_utc
from app.utils.db_utils import serialize_id, to_object_id


class UploadedPrescription:
    COLLECTION = "uploaded_prescriptions"

    @staticmethod
    def _collection():
        return get_collection(UploadedPrescription.COLLECTION)

    @classmethod
    def create(cls, *, image_path, ai_validation, ocr_result, uploaded_by,
               national_id=None, patient_name=None):
        ocr_result = ocr_result or {}
        document = {
            "patient_national_id": (national_id or "").strip() or None,
            "patient_name": patient_name,
            "image_path": image_path,
            "ai_document_validation_result": ai_validation,
            "ocr_text": ocr_result.get("text", "") or "",
            "ocr_source": ocr_result.get("source"),
            "ocr_message": ocr_result.get("message"),
            "status": "open",
            "source": "handwritten_upload",
            "uploaded_by": getattr(uploaded_by, "full_name", None),
            "created_at": now_utc(),
            "dispensed_at": None,
            "dispensed_by": None,
        }
        result = cls._collection().insert_one(document)
        document["_id"] = result.inserted_id
        return serialize_id(document)

    @classmethod
    def get_by_id(cls, upload_id):
        oid = to_object_id(upload_id)
        if oid is None:
            return None
        return serialize_id(cls._collection().find_one({"_id": oid}))

    @classmethod
    def update_ocr_text(cls, upload_id, text):
        oid = to_object_id(upload_id)
        if oid is None:
            return False
        return cls._collection().update_one(
            {"_id": oid}, {"$set": {"ocr_text": text or ""}}
        ).matched_count > 0

    @classmethod
    def dispense(cls, upload_id, pharmacist, ocr_text=None):
        oid = to_object_id(upload_id)
        if oid is None:
            return False
        update = {
            "status": "dispensed",
            "dispensed_at": now_utc(),
            "dispensed_by": getattr(pharmacist, "full_name", "pharmacist"),
        }
        if ocr_text is not None:
            update["ocr_text"] = ocr_text
        return cls._collection().update_one(
            {"_id": oid, "status": "open"}, {"$set": update}
        ).modified_count > 0

    @classmethod
    def list_by_patient(cls, national_id):
        docs = cls._collection().find({"patient_national_id": national_id}).sort("created_at", -1)
        return [serialize_id(doc) for doc in docs]

    @classmethod
    def list_recent(cls, limit=25):
        docs = cls._collection().find().sort("created_at", -1).limit(limit)
        return [serialize_id(doc) for doc in docs]
