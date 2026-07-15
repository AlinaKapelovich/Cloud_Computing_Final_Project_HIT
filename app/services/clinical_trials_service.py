"""clinical_trials_service.py — query ClinicalTrials.gov for related research.

Purpose (official requirement): let doctors and pharmacists consult clinical research
related to a diagnosis, treatment or drug's side-effects.

Provider: ClinicalTrials.gov public REST API v2 (no API key required).

Fallback: on any error or timeout, return an empty but valid result structure so the
UI can show "no related trials / service unavailable" without crashing.
"""
import logging

import requests

from flask import current_app

log = logging.getLogger(__name__)
TIMEOUT = 10


def search_trials(query: str, page_size: int = 5) -> dict:
    """Return {"source", "message", "results":[{nct_id,title,status,url}]}. Never raises."""
    query = (query or "").strip()
    if not query:
        return {"source": "ClinicalTrials.gov", "message": "Please enter a query.", "results": []}

    base = current_app.config.get("CLINICAL_TRIALS_BASE_URL", "https://clinicaltrials.gov/api/v2")
    try:
        response = requests.get(
            f"{base}/studies",
            params={"query.term": query, "pageSize": page_size, "format": "json"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        results = []
        for study in data.get("studies", []):
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status_module = protocol.get("statusModule", {})
            nct_id = identification.get("nctId")
            results.append(
                {
                    "nct_id": nct_id,
                    "title": identification.get("briefTitle") or "Untitled study",
                    "status": status_module.get("overallStatus") or "Unknown",
                    "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "https://clinicaltrials.gov",
                }
            )
        return {
            "source": "ClinicalTrials.gov",
            "message": None if results else "No related clinical trials found.",
            "results": results,
        }
    except Exception as exc:  # noqa: BLE001 - always return a valid empty structure.
        log.warning("ClinicalTrials.gov query failed: %s", exc)
        return {
            "source": "ClinicalTrials.gov",
            "message": "Clinical trials service is currently unavailable. Please try again later.",
            "results": [],
        }
