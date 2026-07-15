"""Doctor controller — dashboard, patient selection, visits, prescriptions.

Thin controller: it validates input and delegates to the visit/prescription models
and the prescription_service (which handles PDF generation and cloud storage).
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.visit_forms import VisitForm
from app.models.prescription import Prescription
from app.models.prescription_item import build_items_from_lists
from app.models.visit import Visit
from app.services import patient_service, prescription_service
from app.services.database_service import get_collection
from app.utils.decorators import role_required

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")


@doctor_bp.route("/")
@login_required
@role_required("doctor")
def dashboard():
    stats = [
        {"label": "Patients", "value": get_collection("patients").count_documents({})},
        {"label": "Prescriptions", "value": get_collection("prescriptions").count_documents({})},
        {"label": "Visits", "value": get_collection("visits").count_documents({})},
    ]
    return render_template("doctor/dashboard.html", stats=stats)


@doctor_bp.route("/patients")
@login_required
@role_required("doctor")
def select_patient():
    query = (request.args.get("q") or "").strip()
    patients = patient_service.list_patients()
    if query:
        q = query.lower()
        patients = [
            p for p in patients
            if q in (p.get("national_id", "").lower())
            or q in (f"{p.get('first_name','')} {p.get('last_name','')}".lower())
        ]
    return render_template("doctor/select_patient.html", patients=patients, query=query)


@doctor_bp.route("/patients/<patient_id>/visit", methods=["GET", "POST"])
@login_required
@role_required("doctor")
def new_visit(patient_id):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        abort(404)

    form = VisitForm()
    if form.validate_on_submit():
        visit = Visit.create(patient, current_user, form.complaints.data, form.diagnosis.data)
        flash("Visit recorded. Now add the prescription.", "success")
        return redirect(url_for("doctor.new_prescription", visit_id=visit["id"]))
    return render_template("doctor/new_visit.html", form=form, patient=patient)


@doctor_bp.route("/visits/<visit_id>/prescription", methods=["GET", "POST"])
@login_required
@role_required("doctor")
def new_prescription(visit_id):
    visit = Visit.get_by_id(visit_id)
    if not visit:
        abort(404)
    patient = patient_service.find_by_national_id(visit.get("patient_national_id"))

    if request.method == "POST":
        diagnosis = request.form.get("diagnosis") or visit.get("diagnosis")
        items = build_items_from_lists(
            request.form.getlist("item_drug"),
            request.form.getlist("item_dosage"),
            request.form.getlist("item_frequency"),
            request.form.getlist("item_duration"),
            request.form.getlist("item_notes"),
        )
        if not items:
            flash("Add at least one medication to the prescription.", "danger")
        else:
            prescription = prescription_service.create_prescription(
                patient=patient, doctor=current_user, diagnosis=diagnosis,
                items=items, visit_id=visit_id,
            )
            flash("Prescription created and PDF generated.", "success")
            return redirect(url_for("doctor.prescription_detail", prescription_id=prescription["id"]))

    return render_template("doctor/new_prescription.html", visit=visit, patient=patient)


@doctor_bp.route("/prescriptions")
@login_required
@role_required("doctor")
def prescriptions_list():
    prescriptions = prescription_service.list_for_doctor(current_user.id)
    return render_template("doctor/prescriptions_list.html", prescriptions=prescriptions)


@doctor_bp.route("/prescriptions/<prescription_id>")
@login_required
@role_required("doctor")
def prescription_detail(prescription_id):
    prescription = prescription_service.get_prescription(prescription_id)
    if not prescription:
        abort(404)
    return render_template("doctor/prescription_detail.html", prescription=prescription)


@doctor_bp.route("/prescriptions/file/<path:filename>")
@login_required
def prescription_pdf_file(filename):
    """Backwards-compatible alias for PDF links stored before the route moved.

    The canonical route is `main.prescription_pdf_file`, which is shared by doctors and
    pharmacists. Kept (without a role restriction) so URLs already persisted in a real
    database keep working for every staff role.
    """
    return redirect(url_for("main.prescription_pdf_file", filename=filename))
