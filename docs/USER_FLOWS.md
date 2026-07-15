# User Flows — MedCloud

Each flow lists the happy path plus the error/fallback states that are actually handled
in the code.

## Authentication (all roles)
- `GET /login` → login form. `POST /login` → verify hashed password.
- Success → redirect to `/dashboard`, which routes to the role dashboard.
- Errors: invalid credentials → flash "Invalid email or password"; unauthenticated access to
  a protected page → redirect to login; wrong role → styled **403** page.

## Admin flow
1. **Dashboard** (`/admin/`) — stat cards (patients, staff, prescriptions) + quick actions.
2. **Patient list** (`/admin/patients`) — table; empty state when none.
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
     ClinicalTrials.gov). Fallbacks render a clear message; the panel never blocks the form.
   - Add medication rows (drug, dosage, frequency, duration, notes).
   - Error: no medication rows → flash "Add at least one medication".
   - Success → prescription created, **PDF generated** and stored → redirect to detail.
5. **Prescription detail** (`/doctor/prescriptions/<id>`) — items, status badge, PDF link,
   PDF storage indicator (Cloudinary vs local fallback).
6. **Prescriptions list** (`/doctor/prescriptions`) — all prescriptions; empty state.

## Pharmacist flow
1. **Dashboard** (`/pharmacist/`) — open/dispensed/uploads counts.
2. **Find patient** (`/pharmacist/search?q=<national_id>`):
   - Not found → empty state with guidance.
   - Found → patient card (with pregnancy/lactation badges), digital prescriptions table,
     uploaded prescriptions table, and a **side-effects consultation panel**
     (`POST /api/consult/side-effects`).
3. **Dispense digital** (`POST /pharmacist/prescriptions/<id>/dispense`):
   - Only `open` prescriptions dispense; already-dispensed → flash warning.
   - On success publishes a dispense event (Kafka stub → console-log fallback).
4. **Upload handwritten** (`/pharmacist/upload`):
   - Validates file type/size (WTForms + config).
   - Pipeline: **AI document validation → OCR → review**. Both steps degrade gracefully.
   - Success → redirect to review page.
5. **Review upload** (`/pharmacist/uploaded/<id>`):
   - Shows the image, the AI validation verdict (valid / invalid / unavailable-manual), and
     the OCR text in an **editable** textarea (manual correction / transcription).
   - **Dispense** (`POST /pharmacist/uploaded/<id>/dispense`) saves the edited text and marks
     dispensed; publishes the dispense event.

## Error & fallback states (cross-cutting)
- Missing API key → service returns a fallback result + the UI shows a clear message.
- External timeout/failure → caught in the service; valid empty structure returned.
- 404 for missing entities; 403 for wrong role; 500 page for unexpected errors.

## Required pages (implemented)
Login · Admin dashboard · Patient list · Patient create/edit · Patient details · Doctor
dashboard · Select patient · New visit · New prescription (with consultation) · Prescription
detail/list · Pharmacist dashboard · Patient lookup · Open/dispensed prescriptions · Upload ·
OCR review · Side-effects consultation · Error pages (403/404/500).
