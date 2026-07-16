"""Pharmacist controller — search, dispense, and handwritten-upload OCR flow.

Thin controller: it coordinates the models (Prescription, UploadedPrescription) and
the service wrappers (ai_document_validator, ocr_service, kafka_service). All external
work and business logic live in the services/models.
"""
from flask import (Blueprint, abort, flash, redirect, render_template, request, url_for)
from flask_login import current_user, login_required

from app.forms.upload_forms import UploadPrescriptionForm
from app.models.prescription import Prescription
from app.models.uploaded_prescription import UploadedPrescription
from app.services import ai_document_validator, kafka_service, ocr_service, patient_service
from app.utils.decorators import role_required
from app.utils.file_utils import absolute_upload_path, save_upload

pharmacist_bp = Blueprint("pharmacist", __name__, url_prefix="/pharmacist")


@pharmacist_bp.route("/")
@login_required
@role_required("pharmacist")
def dashboard():
    counts = Prescription.counts_by_status()
    # Recent uploads are listed here so an upload that was not linked to a national ID
    # is still reachable (the patient search can only find linked ones).
    recent_uploads = UploadedPrescription.list_recent(10)
    stats = [
        {"label": "Open prescriptions", "value": counts["open"]},
        {"label": "Dispensed", "value": counts["dispensed"]},
        {"label": "Uploads", "value": len(UploadedPrescription.list_recent(1000))},
    ]
    return render_template("pharmacist/dashboard.html", stats=stats, recent_uploads=recent_uploads)


@pharmacist_bp.route("/search")
@login_required
@role_required("pharmacist")
def search():
    national_id = (request.args.get("q") or "").strip()
    patient = None
    digital = []
    uploads = []
    if national_id:
        patient = patient_service.find_by_national_id(national_id)
        digital = Prescription.list_by_patient(national_id)
        uploads = UploadedPrescription.list_by_patient(national_id)
    return render_template(
        "pharmacist/search.html",
        national_id=national_id, patient=patient, digital=digital, uploads=uploads,
    )


@pharmacist_bp.route("/prescriptions/<prescription_id>/dispense", methods=["POST"])
@login_required
@role_required("pharmacist")
def dispense_prescription(prescription_id):
    prescription = Prescription.get_by_id(prescription_id)
    if not prescription:
        abort(404)
    if Prescription.dispense(prescription_id, current_user):
        kafka_service.publish_dispensed_event(prescription)  # event (console-log fallback)
        flash("Prescription dispensed.", "success")
    else:
        flash("This prescription is not open and cannot be dispensed.", "warning")
    return redirect(url_for("pharmacist.search", q=prescription.get("patient_national_id", "")))


@pharmacist_bp.route("/upload", methods=["GET", "POST"])
@login_required
@role_required("pharmacist")
def upload():
    form = UploadPrescriptionForm()
    if form.validate_on_submit():
        rel_path = save_upload(form.image.data, subdir="prescriptions_rx")
        if not rel_path:
            flash("Could not save the uploaded file. Please try another image.", "danger")
            return render_template("pharmacist/upload.html", form=form)

        abs_path = str(absolute_upload_path(rel_path))

        # 1) AI document validation runs BEFORE OCR.
        ai_validation = ai_document_validator.validate_document(abs_path)
        # 2) OCR extraction (cloud-first, then Tesseract, then manual).
        ocr_result = ocr_service.extract_text(abs_path)

        patient = patient_service.find_by_national_id(form.national_id.data) if form.national_id.data else None
        patient_name = (
            f"{patient['first_name']} {patient['last_name']}" if patient else None
        )

        upload_doc = UploadedPrescription.create(
            image_path=rel_path,
            ai_validation=ai_validation,
            ocr_result=ocr_result,
            uploaded_by=current_user,
            national_id=form.national_id.data,
            patient_name=patient_name,
        )
        flash("Upload processed. Review the OCR text before dispensing.", "success")
        return redirect(url_for("pharmacist.review_upload", upload_id=upload_doc["id"]))

    return render_template("pharmacist/upload.html", form=form)


@pharmacist_bp.route("/uploaded/<upload_id>")
@login_required
@role_required("pharmacist")
def review_upload(upload_id):
    upload_doc = UploadedPrescription.get_by_id(upload_id)
    if not upload_doc:
        abort(404)
    return render_template("pharmacist/review_upload.html", upload=upload_doc)


@pharmacist_bp.route("/uploaded/<upload_id>/dispense", methods=["POST"])
@login_required
@role_required("pharmacist")
def dispense_upload(upload_id):
    upload_doc = UploadedPrescription.get_by_id(upload_id)
    if not upload_doc:
        abort(404)
    edited_text = request.form.get("ocr_text", upload_doc.get("ocr_text", ""))

    # Enforce the AI/heuristic document validation result before dispensing — never
    # dispense "as if everything is normal" when the image was flagged as invalid.
    validation = upload_doc.get("ai_document_validation_result") or {}
    is_valid = validation.get("valid")

    if is_valid is False:
        flash(
            "This image was flagged as not looking like a prescription document. "
            "Please upload a different image instead of dispensing this one.", "danger",
        )
        return redirect(url_for("pharmacist.review_upload", upload_id=upload_id))

    if is_valid is None:
        manual_confirm_checked = request.form.get("manual_confirm") == "on"
        already_confirmed = bool(upload_doc.get("manual_confirmed"))
        if not (manual_confirm_checked or already_confirmed):
            flash(
                "Document validation was unavailable for this upload. Please check "
                "“I manually confirm that this image is a prescription document” "
                "before dispensing.", "danger",
            )
            return redirect(url_for("pharmacist.review_upload", upload_id=upload_id))
        if manual_confirm_checked and not already_confirmed:
            UploadedPrescription.confirm_manually(upload_id, current_user)

    if UploadedPrescription.dispense(upload_id, current_user, ocr_text=edited_text):
        kafka_service.publish_dispensed_event({**upload_doc, "source": "handwritten_upload"})
        flash("Uploaded prescription dispensed.", "success")
    else:
        UploadedPrescription.update_ocr_text(upload_id, edited_text)
        flash("This upload is already dispensed. OCR text saved.", "warning")
    return redirect(url_for("pharmacist.review_upload", upload_id=upload_id))
