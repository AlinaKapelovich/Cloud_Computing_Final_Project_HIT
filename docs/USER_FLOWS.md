# User Flows — MedCloud

Each flow lists the happy path plus the error/fallback states that are actually handled
in the code.

## Authentication (all roles)
- `GET /login` → login form. `POST /login` → verify hashed password.
- Success → redirect to `/dashboard`, which routes to the role dashboard.
- Errors: invalid credentials → flash "Invalid email or password"; unauthenticated access to
  a protected page → redirect to login; wrong role → styled **403** page.

## Admin flow
1. **Dashboard** (`/admin/`) — stat cards (patients, prescriptions — read-only oversight
   only; no staff/user-account management, which is not an Admin requirement) + quick
   actions, all linking to real, working pages.
2. **Patient list** (`/admin/patients`) — table with a **search box** (name or national
   ID, `?q=`); distinct empty states for "no patients yet" vs. "no results for this search".
3. **Create patient** (`/admin/patients/new`) — WTForms validation.
   - Error: duplicate national ID → flash error, form redisplayed.
   - Photo upload optional; stored under `uploads/patients/`.
4. **Edit patient** (`/admin/patients/<id>/edit`) — pre-filled form; keeps existing photo if
   none uploaded.
5. **Patient profile** (`/admin/patients/<id>`) — details + **calculated age**.

## Doctor flow
1. **Dashboard** (`/doctor/`).
2. **Select patient** (`/doctor/patients`) — search by name/national ID; empty state.
3. **New visit** (`/doctor/patients/<id>/visit`) — complaints + diagnosis (required).
4. **New prescription** (`/doctor/visits/<visit_id>/prescription`):
   - **Diagnosis consultation panel** — calls `POST /api/consult/diagnosis` (Tavily +
     ClinicalTrials.gov; Doctor-only, enforced server-side). Fallbacks render a clear
     message; the panel never blocks the form.
   - Add medication rows (drug, dosage, frequency, duration, notes).
   - Error: no medication rows → flash "Add at least one medication".
   - Success → prescription created, **PDF generated** and stored → redirect to detail.
5. **Prescription detail** (`/doctor/prescriptions/<id>`) — items, status badge, PDF link,
   PDF storage indicator (Cloudinary vs local fallback).
6. **Prescriptions list** (`/doctor/prescriptions`) — all prescriptions; empty state.

## Pharmacist flow
1. **Dashboard** (`/pharmacist/`) — open/dispensed/uploads counts + a **recent uploads**
   table, so an upload not linked to a national ID stays reachable.
2. **Side-effects consultation** — the panel (`POST /api/consult/side-effects`,
   Pharmacist-only, enforced server-side) is shown directly on `/pharmacist/search`,
   **independent of whether a patient search has been run** — it is a drug-name lookup,
   not tied to a specific patient record.
3. **Find patient** (`/pharmacist/search?q=<national_id>`):
   - Not found → empty state with guidance.
   - Found → patient card (with pregnancy/lactation badges), digital prescriptions table
     showing the **actual medication names/dosages** for each prescription (not just an
     item count), and an uploaded-prescriptions table.
4. **Dispense digital** (`POST /pharmacist/prescriptions/<id>/dispense`):
   - Only `open` prescriptions dispense; already-dispensed → flash warning.
   - On success publishes a dispense event (Kafka stub → console-log fallback).
5. **Upload handwritten** (`/pharmacist/upload`):
   - Validates file type/size (WTForms + config).
   - Pipeline: **AI document validation → OCR (image-to-text, not translation) → review**.
     Both steps degrade gracefully through their fallback chains.
   - Success → redirect to review page.
6. **Review upload** (`/pharmacist/uploaded/<id>`):
   - Shows the image, the AI validation verdict, and the OCR text in an **editable**
     textarea (manual correction / transcription).
   - **Enforcement, not just display:** if the document was flagged **invalid**, the
     dispense form is replaced with a clear error and a link back to upload a different
     image. If validation was **unavailable**, dispensing requires checking "I manually
     confirm that this image is a prescription document" — the confirmation (who, when)
     is stored on the record.
   - **Dispense** (`POST /pharmacist/uploaded/<id>/dispense`) saves the edited text and marks
     dispensed; publishes the dispense event.

## Error & fallback states (cross-cutting)
- Missing API key → service returns a fallback result + the UI shows a clear message.
- External timeout/failure → caught in the service; valid empty structure returned.
- 404 for missing entities; 403 for wrong role or wrong consultation endpoint; 413 for an
  oversized upload; a styled page for an expired CSRF token; 500 for unexpected errors.
  All error pages are styled — none fall through to a raw Werkzeug/stack-trace page.

## Required pages (implemented)
Login · Admin dashboard · Patient list (with search) · Patient create/edit · Patient
details · Doctor dashboard · Select patient · New visit · New prescription (with
diagnosis consultation) · Prescription detail/list · Pharmacist dashboard (with recent
uploads) · Patient lookup (with side-effects consultation) · Open/dispensed prescriptions
(with medication names) · Upload · OCR review (with validation enforcement) · Error pages
(403/404/413/500/CSRF).
