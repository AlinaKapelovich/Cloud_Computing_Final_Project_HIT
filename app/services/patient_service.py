"""patient_service.py — business logic for patient management.

Sits between the Admin controller and the Patient model. Handles cross-cutting
concerns like photo upload and uniqueness checks, keeping the controller thin.
"""
from app.models.patient import Patient
from app.utils.file_utils import save_upload


def list_patients():
    return Patient.list_all()


def get_patient(patient_id):
    return Patient.get_by_id(patient_id)


def find_by_national_id(national_id: str):
    return Patient.get_by_national_id(national_id)


def create_patient(form_data: dict, photo_file=None):
    """Create a patient. Returns (patient, error_message)."""
    national_id = (form_data.get("national_id") or "").strip()
    if Patient.national_id_exists(national_id):
        return None, "A patient with this National ID already exists."

    photo_path = save_upload(photo_file, subdir="patients") if photo_file else None
    if photo_path:
        form_data = {**form_data, "photo": photo_path}

    patient = Patient.create(form_data)
    return patient, None


def update_patient(patient_id, form_data: dict, photo_file=None):
    """Update a patient. Returns (ok, error_message)."""
    national_id = (form_data.get("national_id") or "").strip()
    if Patient.national_id_exists(national_id, exclude_id=patient_id):
        return False, "Another patient already uses this National ID."

    existing = Patient.get_by_id(patient_id)
    if not existing:
        return False, "Patient not found."

    photo_path = save_upload(photo_file, subdir="patients") if photo_file else None
    # Keep the previous photo if no new one was uploaded.
    form_data = {**form_data, "photo": photo_path or existing.get("photo", "")}

    ok = Patient.update(patient_id, form_data)
    return ok, None if ok else "Could not update patient."
