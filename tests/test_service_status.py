"""service_status.py — accuracy of the Fallback / Configured / Verified tri-state.

Regression coverage for two specific bugs fixed in this pass:
  1. OCR status must recognize HUGGINGFACE_API_TOKEN, not only OCR_API_URL.
  2. ClinicalTrials.gov must never be reported "Verified" merely for being a public API.
"""
from app.utils.service_status import service_status_summary


def _by_name(summary, name):
    return next(row for row in summary if row["name"] == name)


def test_all_services_are_fallback_with_no_configuration(app):
    with app.test_request_context():
        summary = service_status_summary(app.config)
    for row in summary:
        assert row["status"] in ("Fallback", "Configured")  # DB/trials are always "attemptable"
    assert _by_name(summary, "PDF storage")["status"] == "Fallback"
    assert _by_name(summary, "Diagnosis search")["status"] == "Fallback"
    assert _by_name(summary, "OCR")["status"] == "Fallback"
    assert _by_name(summary, "AI document validator")["status"] == "Fallback"


def test_ocr_recognizes_huggingface_token_not_only_generic_url(app):
    """Regression: previously only OCR_API_URL was checked, ignoring HUGGINGFACE_API_TOKEN."""
    app.config["HUGGINGFACE_API_TOKEN"] = "fake-token"
    app.config["OCR_API_URL"] = ""
    with app.test_request_context():
        row = _by_name(service_status_summary(app.config), "OCR")
    assert row["status"] == "Configured"
    assert "Hugging Face" in row["detail"]


def test_ocr_still_recognizes_generic_cloud_endpoint(app):
    app.config["HUGGINGFACE_API_TOKEN"] = ""
    app.config["OCR_API_URL"] = "https://example-ocr.test/extract"
    with app.test_request_context():
        row = _by_name(service_status_summary(app.config), "OCR")
    assert row["status"] == "Configured"
    assert row["detail"] == "Generic cloud OCR"


def test_clinical_trials_is_never_verified_just_for_being_public(app):
    """Regression: a keyless public API must not be reported as more than 'Configured'."""
    app.config["LIVE_VERIFIED_SERVICES"] = ""
    with app.test_request_context():
        row = _by_name(service_status_summary(app.config), "Clinical trials")
    assert row["status"] == "Configured"
    assert row["status"] != "Verified"


def test_configured_credentials_alone_do_not_count_as_verified(app):
    """Having an API key present must show 'Configured', never 'Verified', by itself."""
    app.config["TAVILY_API_KEY"] = "fake-key"
    app.config["LIVE_VERIFIED_SERVICES"] = ""
    with app.test_request_context():
        row = _by_name(service_status_summary(app.config), "Diagnosis search")
    assert row["status"] == "Configured"


def test_explicit_live_verified_services_elevates_to_verified(app):
    """Only an explicit, human-set LIVE_VERIFIED_SERVICES entry can produce 'Verified'."""
    app.config["TAVILY_API_KEY"] = "fake-key"
    app.config["LIVE_VERIFIED_SERVICES"] = "tavily,clinicaltrials"
    with app.test_request_context():
        summary = service_status_summary(app.config)
    assert _by_name(summary, "Diagnosis search")["status"] == "Verified"
    assert _by_name(summary, "Clinical trials")["status"] == "Verified"
    assert _by_name(summary, "PDF storage")["status"] == "Fallback"  # untouched


def test_verified_without_configuration_does_not_apply(app):
    """A stale/incorrect LIVE_VERIFIED_SERVICES entry must not override a missing key."""
    app.config["TAVILY_API_KEY"] = ""
    app.config["LIVE_VERIFIED_SERVICES"] = "tavily"
    with app.test_request_context():
        row = _by_name(service_status_summary(app.config), "Diagnosis search")
    assert row["status"] == "Fallback"  # no key configured -> cannot be "Verified"


def test_pytest_never_sets_live_verified_services_by_default(app):
    """Sanity check: the test suite itself must never accidentally claim a live verification."""
    with app.test_request_context():
        summary = service_status_summary(app.config)
    assert all(row["status"] != "Verified" for row in summary)
