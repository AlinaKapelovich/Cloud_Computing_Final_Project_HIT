"""prescription_service.py — business logic for prescriptions.

Orchestrates the create flow: persist the prescription, generate its PDF, store the
PDF (Cloudinary or local fallback), and record where the PDF lives. Keeps the doctor
controller thin.
"""
import logging

from app.models.prescription import Prescription
from app.services import cloud_storage_service, pdf_service

log = logging.getLogger(__name__)


def create_prescription(*, patient, doctor, diagnosis, items, visit_id=None):
    """Create a digital prescription, generate and store its PDF, return it refreshed."""
    prescription = Prescription.create(
        patient=patient, doctor=doctor, diagnosis=diagnosis, items=items, visit_id=visit_id
    )
    _generate_and_store_pdf(prescription)
    return Prescription.get_by_id(prescription["id"])


def _generate_and_store_pdf(prescription: dict) -> None:
    """Generate the PDF and store it, tolerating failures without breaking the flow."""
    try:
        local_path = pdf_service.generate_prescription_pdf(prescription)
    except Exception as exc:  # noqa: BLE001 - a PDF failure must not lose the prescription.
        log.error("PDF generation failed for %s: %s", prescription.get("id"), exc)
        return

    stored = cloud_storage_service.store_pdf(local_path, prescription["id"])
    Prescription.set_pdf(
        prescription["id"],
        pdf_path=str(local_path),          # always keep a local copy path
        pdf_url=stored.get("url"),
        pdf_storage=stored.get("storage"),
    )


def get_prescription(prescription_id):
    return Prescription.get_by_id(prescription_id)


def list_for_doctor(doctor_id):
    return Prescription.list_by_doctor(doctor_id)
