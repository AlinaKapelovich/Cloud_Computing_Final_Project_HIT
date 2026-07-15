"""API controller — JSON endpoints consumed by the frontend (fetch/AJAX).

Demonstrates a REST-style JSON API layered on top of HTTP, alongside the
server-rendered HTML views. Consultation endpoints call the service wrappers
(search / clinical trials) and log each query. Controllers stay thin — no external
API calls happen here directly.
"""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.models.service_query_log import ServiceQueryLog
from app.services import clinical_trials_service, search_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/ping")
def ping():
    return jsonify({"status": "ok", "service": "medcloud-api"}), 200


def _query_from_request() -> str:
    data = request.get_json(silent=True) or {}
    return (data.get("query") or request.form.get("query") or "").strip()


@api_bp.route("/consult/diagnosis", methods=["POST"])
@login_required
def consult_diagnosis():
    """Doctor diagnosis consultation: web/drug search + related clinical trials."""
    query = _query_from_request()
    search = search_service.consult_diagnosis(query)
    trials = clinical_trials_service.search_trials(query)

    ServiceQueryLog.log(service="diagnosis_search", query=query,
                        source=search.get("source", "unknown"),
                        result_count=len(search.get("results", [])), user=current_user)
    ServiceQueryLog.log(service="clinical_trials", query=query,
                        source="ClinicalTrials.gov",
                        result_count=len(trials.get("results", [])), user=current_user)

    return jsonify({"query": query, "search": search, "trials": trials}), 200


@api_bp.route("/consult/side-effects", methods=["POST"])
@login_required
def consult_side_effects():
    """Pharmacist side-effects consultation: drug side-effects + related clinical trials."""
    query = _query_from_request()
    side_effects = search_service.consult_side_effects(query)
    trials = clinical_trials_service.search_trials(f"{query} adverse effects")

    ServiceQueryLog.log(service="side_effects", query=query,
                        source=side_effects.get("source", "unknown"),
                        result_count=len(side_effects.get("results", [])), user=current_user)
    ServiceQueryLog.log(service="clinical_trials", query=query,
                        source="ClinicalTrials.gov",
                        result_count=len(trials.get("results", [])), user=current_user)

    return jsonify({"query": query, "side_effects": side_effects, "trials": trials}), 200
