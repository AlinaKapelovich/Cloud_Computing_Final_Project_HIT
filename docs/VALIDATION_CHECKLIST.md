# Validation Checklist — MedCloud

## Automated tests
- [x] `python -m pytest` (run three consecutive times) → **78 passed, 1 deselected**
      each time, **zero real network calls and zero real Tesseract invocations** (see
      `tests/conftest.py::block_real_network` and `::block_real_tesseract` — enforced
      even if the machine running the suite has internet access, real API keys, or a
      real Tesseract binary installed). The 1 deselected test is the optional
      `@pytest.mark.integration` real-Tesseract check (see `tests/test_ocr_provider.py`),
      excluded by default (`pytest.ini: addopts = -m "not integration"`) and runnable
      explicitly with `pytest -m integration`.
- [x] `python -m compileall app run.py scripts` → clean.
- [x] `pip check` → no broken requirements.
- [x] Regression test: pharmacist can open a locally-stored prescription PDF (was a 403 bug).
- [x] Route-render sweep: every no-argument page, for every role, returns < 500.
- [x] Mocked provider tests: Hugging Face OCR (success / cold-start / failure fallback),
      Tavily, OpenFDA, ClinicalTrials.gov, Cloudinary (success + local fallback).
- [x] AI document validator enforcement tests: valid / invalid / unavailable-blocked /
      unavailable-with-manual-confirmation.
- [x] Consultation RBAC tests: Doctor-only diagnosis endpoint, Pharmacist-only
      side-effects endpoint, cross-role denial for both.
- [x] Service-status accuracy tests: OCR recognizes `HUGGINGFACE_API_TOKEN` (not only
      `OCR_API_URL`); ClinicalTrials.gov never reports "Verified" just for being public;
      "Configured" (credentials present) is never conflated with "Verified" (a real
      call confirmed) — see `tests/test_service_status.py`.
- [x] Demo-seeding tests: `SEED_DEMO_USERS=true` against a non-demo-mode database (the
      exact scenario `docker-compose.yml` now relies on) seeds all three roles with
      working passwords — see `tests/test_bootstrap_seeding.py`.

## Functional
- [x] App starts with no credentials (`python run.py`).
- [x] Demo users seeded automatically in demo mode (no `MONGO_URI`); a real database
      requires an explicit `SEED_DEMO_USERS=true` to get demo accounts (never silent).
- [x] Admin: create/list/**search**/edit/view patients; duplicate national ID rejected.
- [x] Patient age is calculated from birth date (never stored as a frozen value).
- [x] Doctor: select patient → visit → diagnosis consultation → prescription with items.
- [x] Prescription PDF generated; downloadable link shown; openable by both Doctor and
      Pharmacist (regression-tested).
- [x] Pharmacist: search by national ID; see the actual medications on each prescription
      (not just a count); dispense open prescription.
- [x] Pharmacist: side-effects consultation reachable without first finding a patient.
- [x] Upload handwritten → AI validation → OCR (image-to-text, not translation) → review
      → dispense, **with enforcement**: invalid documents block dispensing; validation-
      unavailable requires an explicit manual-confirmation checkbox before dispensing.
- [x] Diagnosis (Doctor-only) and side-effects (Pharmacist-only) consultations return
      results/messages and are blocked cross-role at the backend, not just hidden in the UI.

## MVC separation
- [x] Controllers are thin; no external API calls in controllers.
- [x] Services wrap every external API; business logic in services.
- [x] Models hold data + MongoDB access only.
- [x] Templates contain no API calls; static assets separate from views.

## Cloud services (see docs/CLOUD_SERVICES.md for full detail)
- [x] MongoDB Atlas via wrapper (+ in-memory fallback) — not tested live (no MONGO_URI
      available in this environment); fallback path exercised by the entire test suite.
- [x] Cloudinary via wrapper (+ local fallback) — not tested live; mocked success test
      exercises the real SDK call signature.
- [x] Tavily (+ OpenFDA fallback) — not tested live; both mocked with realistic responses.
- [x] ClinicalTrials.gov (empty-valid on failure) — not tested live (keyless, but this
      sandbox has no outbound network); mocked success + graceful-failure tests exist.
- [x] Hugging Face OCR (TrOCR) (+ generic cloud endpoint + Tesseract + manual fallback) —
      not tested live; mocked success/cold-start/failure tests exist.
- [x] AI validator: hosted vision (+ heuristic + manual-confirmation fallback) — not
      tested live; heuristic path is exercised directly (no mock needed, it's local code).

## Fallback (each service disabled)
- [x] No `MONGO_URI` → in-memory DB, app works.
- [x] No Cloudinary keys → PDF stored locally, link works for both Doctor and Pharmacist.
- [x] No `TAVILY_API_KEY` → OpenFDA / message.
- [x] No `HUGGINGFACE_API_TOKEN`/`OCR_API_URL` → Tesseract/manual message.
- [x] No vision key → heuristic validation; if even that can't decide, blocks dispensing
      until manually confirmed.
- [x] External timeout/error → valid structure + UI message, no crash.

## UI/UX
- [x] Consistent medical dashboard style; no unstyled pages.
- [x] Sidebar navigation per role; responsive layout.
- [x] Status badges, empty states, success/error alerts.
- [x] All pages render (route-render sweep: 0 server errors across roles).
- [x] **No "Coming soon" placeholders anywhere** — every action card links to a real,
      working route; the shared `action_card` macro requires a real endpoint.
- [x] No misleading Admin card/stat for a feature that doesn't exist (removed the
      "Clinical workflow" card and the "Staff accounts" stat — Admin's scope is patients).

## Security / config
- [x] Passwords hashed (Werkzeug); role-based access enforced on pages AND on the
      consultation API endpoints (not just hidden buttons in templates).
- [x] CSRF protection on forms; `.env` git-ignored; expired-CSRF shows a styled page.
- [x] No secrets hardcoded; `.env.example` documents every variable, including the new
      `HUGGINGFACE_API_TOKEN`, `SEED_DEMO_USERS`, `DEMO_PASSWORD`.
- [x] `FLASK_DEBUG` defaults to **off**; a fresh clone with no `.env` never exposes the
      interactive debugger.
- [x] Demo users are never silently seeded into a real, persistent database — only into
      the in-memory demo database by default, or explicitly via `SEED_DEMO_USERS=true`.
- [x] Oversized uploads (413) show a styled page, not Werkzeug's raw error page.

## Docker / deployment
- [x] `Dockerfile`, `docker-compose.yml`, `render.yaml`, `.dockerignore` present.
- [x] Docker installs Tesseract for the OCR fallback.
- [x] `docker-compose.yml` sets `SEED_DEMO_USERS: "true"` and `DEMO_PASSWORD: "demo1234"`
      explicitly (a real `MONGO_URI` is configured for the `mongo` service, so without
      this the login page would be unusable on a fresh container — see
      `tests/test_bootstrap_seeding.py` for the underlying logic proof).
- [ ] **NOT VERIFIED:** `docker compose config`, `docker build .`, `docker compose up --build`
      were **not executed** — Docker is not installed in this development environment
      (checked: no `docker` binary, no Docker Desktop process running). Run these on a
      machine with Docker before the defense, and confirm all three demo logins work on
      a fresh container per `docs/LIVE_VERIFICATION.md`.
- [ ] **NOT VERIFIED:** Render deployment. No deployed URL exists yet — do not claim a
      live deployment until one has actually been created and its `/health`, login, PDF
      access, and upload flow have been checked against the real deployed URL (record in
      `docs/LIVE_VERIFICATION.md`).

## Submission packaging
- [x] `scripts/build_submission_zip.py` builds a clean archive containing only
      `app/`, `docs/`, `tests/`, `scripts/`, and configuration templates. Verified by
      running it: 106 files written, confirmed absent from the archive: `.git`, `.env`,
      `uploads/`, `generated_pdfs/`, `__pycache__`, `.pytest_cache`, virtual
      environments, and the course-material folders.

## UI/UX verification method
- [x] Every page rendered and asserted via the test client (no 500s, styled error pages).
- [x] Templates/CSS reviewed; no raw JSON/dict output to users; no unstyled forms; no
      "Coming soon" text anywhere in the rendered app.
- [ ] **NOT DONE:** visual browser screenshot pass (the Claude-in-Chrome extension was
      not connected in this environment). Do the manual demo path in `README.md` yourself
      before the defense to see the actual rendered pages.

## Live cloud verification
- [ ] **NOT DONE:** `docs/LIVE_VERIFICATION.md` — a checklist of real, successful calls
      to each mandatory service (MongoDB Atlas persistence, Cloudinary PDF upload,
      Tavily, Hugging Face OCR with a real image, ClinicalTrials.gov), each requiring a
      recorded date and result. Every row is currently "not yet tested" — this sandbox
      has no outbound internet access. Complete this on a machine with real credentials
      and internet access before claiming any provider works live.

## Defense readiness
- [x] `DEFENSE_GUIDE.md` covers all required concepts + how to explain a random file.
- [x] Every folder/file maps to a role in MVC and a requirement.
- [x] Footer shows a three-state **Fallback / Configured / Verified** status per service
      (see `app/utils/service_status.py`), never claiming "live" from configuration
      alone — "Verified" only ever comes from a human completing
      `docs/LIVE_VERIFICATION.md` and setting `LIVE_VERIFIED_SERVICES`.
