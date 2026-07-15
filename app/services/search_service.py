"""search_service.py — diagnosis and drug consultation via cloud search.

Purpose: let a doctor consult a diagnosis and a pharmacist check drug side-effects,
using a real-time cloud search service.

Provider strategy (fallback chain):
  1. Tavily (primary real-time web search) — requires TAVILY_API_KEY.
  2. OpenFDA drug label API (keyless) — used as a fallback for drug-related queries.
  3. A clear, user-friendly message when nothing is available.

Every result is a dict: {"source": str, "message": str|None, "results": [ ... ]}.
This function never raises — on any error it degrades to the next option.
"""
import logging

import requests

from flask import current_app

log = logging.getLogger(__name__)
TIMEOUT = 8


def consult_diagnosis(query: str) -> dict:
    """Consult general medical information for a diagnosis/symptom query."""
    query = (query or "").strip()
    if not query:
        return {"source": "none", "message": "Please enter a query.", "results": []}

    key = current_app.config.get("TAVILY_API_KEY")
    if key:
        result = _tavily(query, key)
        if result is not None:
            return result

    # Fallback: OpenFDA drug label (works best when the query mentions a drug).
    result = _openfda_label(query, field="indications_and_usage")
    if result is not None and result["results"]:
        return result

    return {
        "source": "unavailable",
        "message": "Live diagnosis search is disabled. Set TAVILY_API_KEY to enable Tavily search.",
        "results": [],
    }


def consult_side_effects(drug: str) -> dict:
    """Consult drug side-effects. Tavily first, then OpenFDA adverse reactions."""
    drug = (drug or "").strip()
    if not drug:
        return {"source": "none", "message": "Please enter a drug name.", "results": []}

    key = current_app.config.get("TAVILY_API_KEY")
    if key:
        result = _tavily(f"{drug} side effects", key)
        if result is not None and result["results"]:
            return result

    result = _openfda_label(drug, field="adverse_reactions")
    if result is not None:
        return result

    return {
        "source": "unavailable",
        "message": "Side-effect lookup is unavailable right now. Please consult the drug label manually.",
        "results": [],
    }


def _tavily(query: str, key: str):
    """Call the Tavily search API. Returns a result dict, or None on failure."""
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": key, "query": query, "max_results": 5, "search_depth": "basic"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        results = [
            {"title": item.get("title"), "snippet": item.get("content"), "url": item.get("url")}
            for item in data.get("results", [])
        ]
        return {
            "source": "Tavily",
            "message": None if results else "No results found.",
            "results": results,
        }
    except Exception as exc:  # noqa: BLE001 - degrade to the next provider.
        log.warning("Tavily search failed: %s", exc)
        return None


def _openfda_label(query: str, field: str):
    """Query the OpenFDA drug label API. Returns a result dict, or None on failure."""
    base = current_app.config.get("OPENFDA_BASE_URL", "https://api.fda.gov")
    try:
        response = requests.get(
            f"{base}/drug/label.json",
            params={"search": f"{field}:{query}", "limit": 3},
            timeout=TIMEOUT,
        )
        if response.status_code == 404:
            return {"source": "OpenFDA", "message": "No matching drug labels found.", "results": []}
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("results", []):
            openfda = item.get("openfda", {})
            name = (openfda.get("brand_name") or openfda.get("generic_name") or ["Drug label"])[0]
            text = (item.get(field) or [""])[0]
            results.append({"title": name, "snippet": _clip(text, 400), "url": "https://open.fda.gov"})
        return {
            "source": "OpenFDA",
            "message": None if results else "No matching drug labels found.",
            "results": results,
        }
    except Exception as exc:  # noqa: BLE001 - degrade gracefully.
        log.warning("OpenFDA lookup failed: %s", exc)
        return None


def _clip(text: str, length: int) -> str:
    text = str(text or "").strip()
    return text if len(text) <= length else text[: length - 1] + "…"
