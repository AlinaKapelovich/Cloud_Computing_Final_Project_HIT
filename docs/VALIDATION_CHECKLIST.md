# Validation Checklist — MedCloud

## Automated tests
- [x] `python -m pytest` → **43 passed** (no credentials required).
- [x] `python -m compileall app run.py scripts` → clean.
- [x] `pip check` → no broken requirements.
- [x] Regression test: pharmacist can open a locally-stored prescription PDF (was a 403 bug).
- [x] Render sweep: every no-argument page, for every role, returns < 500.

## Functional
- [x] App starts with no credentials (`python run.py`).
- [x] Demo users seeded; all three roles can log in.
- [x] Admin: create/list/edit/view patients; duplicate national ID rejected.
- [x] Patient age is calculated from birth date.
- [x] Doctor: select patient → visit → prescription with items.
- [x] Prescription PDF generated; downloadable link shown.
- [x] Pharmacist: search by national ID; dispense open prescription.
- [x] Upload handwritten → AI validation → OCR → review → dispense.
- [x] Diagnosis and side-effects consultations return results/messages.

## MVC separation
- [x] Controllers are thin; no external API calls in controllers.
- [x] Services wrap every external API; business logic in services.
- [x] Models hold data + MongoDB access only.
- [x] Templates contain no API calls; static assets separate from views.

## Cloud services
- [x] MongoDB Atlas via wrapper (+ in-memory fallback).
- [x] Cloudinary via wrapper (+ local fallback).
- [x] Tavily (+ OpenFDA fallback).
- [x] ClinicalTrials.gov (empty-valid on failure).
- [x] Cloud OCR (+ Tesseract + manual fallback).
- [x] AI validator (+ heuristic + manual fallback).

## Fallback (each service disabled)
- [x] No `MONGO_URI` → in-memory DB, app works.
- [x] No Cloudinary keys → PDF stored locally, link works.
- [x] No `TAVILY_API_KEY` → OpenFDA / message.
- [x] No OCR key → Tesseract/manual message.
- [x] No vision key → heuristic validation.
- [x] External timeout/error → valid structure + UI message, no crash.

## UI/UX
- [x] Consistent medical dashboard style; no unstyled pages.
- [x] Sidebar navigation per role; responsive layout.
- [x] Status badges, empty states, success/error alerts.
- [x] All pages render (route-render sweep: 0 server errors across roles).

## Security / config
- [x] Passwords hashed (Werkzeug); role-based access enforced.
- [x] CSRF protection on forms; `.env` git-ignored.
- [x] No secrets hardcoded; `.env.example` documents every variable.

## Docker / deployment
- [x] `Dockerfile`, `docker-compose.yml`, `render.yaml`, `.dockerignore` present.
- [x] Docker installs Tesseract for the OCR fallback.
- [ ] **NOT VERIFIED:** `docker compose config`, `docker build .`, `docker compose up --build`
      were **not executed** — Docker is not installed on the development machine. Run these on a
      machine with Docker before the defense.

## UI/UX verification method
- [x] Every page rendered and asserted via the test client (no 500s, styled error pages).
- [x] Templates/CSS reviewed; no raw JSON/dict output to users; no unstyled forms.
- [ ] **NOT DONE:** visual browser screenshot pass (do the manual demo path in README/report).

## Defense readiness
- [x] `DEFENSE_GUIDE.md` covers all required concepts + how to explain a random file.
- [x] Every folder/file maps to a role in MVC and a requirement.
- [x] Footer shows live vs fallback service status.
