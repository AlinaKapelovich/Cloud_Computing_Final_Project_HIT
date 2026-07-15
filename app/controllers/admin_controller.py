"""Admin controller — dashboard and patient management (CRUD).

Thin controller: validates the patient form, delegates to patient_service, and
renders templates. All data logic lives in the model/service layers.
"""
from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import login_required

from app.forms.patient_forms import PatientForm
from app.services import patient_service
from app.services.database_service import get_collection
from app.utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@role_required("admin")
def dashboard():
    stats = [
        {"label": "Patients", "value": get_collection("patients").count_documents({}),
         "endpoint": "admin.patients_list"},
        {"label": "Staff accounts", "value": get_collection("users").count_documents({}),
         "endpoint": None},
        {"label": "Prescriptions", "value": get_collection("prescriptions").count_documents({}),
         "endpoint": None},
    ]
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/patients")
@login_required
@role_required("admin")
def patients_list():
    patients = patient_service.list_patients()
    return render_template("admin/patients_list.html", patients=patients)


@admin_bp.route("/patients/new", methods=["GET", "POST"])
@login_required
@role_required("admin")
def patient_create():
    form = PatientForm()
    if form.validate_on_submit():
        patient, error = patient_service.create_patient(_form_to_dict(form), form.photo.data)
        if error:
            flash(error, "danger")
        else:
            flash("Patient created successfully.", "success")
            return redirect(url_for("admin.patient_detail", patient_id=patient["id"]))
    return render_template("admin/patient_form.html", form=form, mode="create")


@admin_bp.route("/patients/<patient_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def patient_edit(patient_id):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        abort(404)

    form = PatientForm(data=_patient_to_form(patient))
    if form.validate_on_submit():
        ok, error = patient_service.update_patient(patient_id, _form_to_dict(form), form.photo.data)
        if error:
            flash(error, "danger")
        else:
            flash("Patient updated successfully.", "success")
            return redirect(url_for("admin.patient_detail", patient_id=patient_id))
    return render_template("admin/patient_form.html", form=form, mode="edit", patient=patient)


@admin_bp.route("/patients/<patient_id>")
@login_required
@role_required("admin")
def patient_detail(patient_id):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        abort(404)
    return render_template("admin/patient_detail.html", patient=patient)


# ----- small mapping helpers keep the routes readable -----
def _form_to_dict(form: PatientForm) -> dict:
    return {
        "national_id": form.national_id.data,
        "first_name": form.first_name.data,
        "last_name": form.last_name.data,
        "gender": form.gender.data,
        "pregnancy_status": form.pregnancy_status.data,
        "lactation_status": form.lactation_status.data,
        "birth_date": form.birth_date.data,
        "email": form.email.data,
        "phone": form.phone.data,
    }


def _patient_to_form(patient: dict) -> dict:
    from app.utils.date_utils import parse_date

    return {
        "national_id": patient.get("national_id"),
        "first_name": patient.get("first_name"),
        "last_name": patient.get("last_name"),
        "gender": patient.get("gender"),
        "pregnancy_status": patient.get("pregnancy_status"),
        "lactation_status": patient.get("lactation_status"),
        "birth_date": parse_date(patient.get("birth_date")),
        "email": patient.get("email"),
        "phone": patient.get("phone"),
    }
