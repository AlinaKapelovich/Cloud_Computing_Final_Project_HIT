# PRD — MedCloud (Product Requirements Document)

## 1. Overview
MedCloud is a medical **prescription management** web application for the HIT Cloud
Computing final project (course 43008, Healthcare theme). It lets a clinic manage
patients, write and store prescriptions in the cloud, dispense them, digitise handwritten
prescriptions with OCR, and consult external medical knowledge sources.

**Source of truth:** the official project requirements PDF. This PRD reconciles those
requirements with the locked technical decisions below.

## 2. Roles
- **Admin** — manages patient records.
- **Doctor** — records visits, writes prescriptions, generates PDFs, consults sources.
- **Pharmacist** — searches patients, dispenses prescriptions, uploads/OCRs handwritten
  prescriptions, consults drug side-effects.

## 3. Functional requirements

### 3.1 Admin
- Create patient records; view patient list; edit patient details; view patient profile.
- Patient fields: national ID, first name, last name, gender, pregnancy status, lactation
  status, **birth date (age is calculated, not stored)**, photo, email, phone.

### 3.2 Doctor
- Select a patient; create a visit (complaints, diagnosis).
- Consult a diagnosis using a cloud/search service (Tavily + ClinicalTrials.gov).
- Create a prescription; add prescription items (drug, dosage, frequency, duration, notes).
- Generate a prescription **PDF**; save it via **cloud storage** (Cloudinary) with local
  fallback; store the URL/path in the database.
- View created prescriptions.

### 3.3 Pharmacist
- Search patient by national ID.
- View open and dispensed prescriptions; dispense an open prescription.
- Upload an image of a handwritten prescription; run **AI document validation** then **OCR**;
  review/correct the extracted text; dispense the uploaded prescription.
- Consult drug **side-effects** using a cloud service.

## 4. Non-functional requirements
- **Fallback-first:** every external service has a documented fallback; the app runs
  end-to-end with zero credentials.
- **Security:** hashed passwords (Werkzeug), role-based access, CSRF protection, no
  hardcoded secrets, `.env` git-ignored.
- **Clean MVC** separation; thin controllers; services wrap all external APIs.
- **Good UI/UX:** consistent medical-dashboard style, responsive, status badges, empty states.
- **Explainability / defense readiness:** every file maps to a role in MVC and to a
  requirement; concepts documented in `DEFENSE_GUIDE.md`.
- **PIV methodology:** Planning (docs) → Implementation (milestones) → Validation (smoke tests).

## 5. Mandatory cloud services (all wrapped, all with fallbacks)
| Service | Wrapper | Fallback |
|---|---|---|
| Cloud NoSQL database | MongoDB Atlas via `database_service.py` | In-memory mongomock |
| PDF/blob storage | Cloudinary via `cloud_storage_service.py` | Local `generated_pdfs/` |
| Diagnosis search | Tavily via `search_service.py` | OpenFDA → message |
| Clinical research | ClinicalTrials.gov via `clinical_trials_service.py` | Empty valid structure |
| OCR | Cloud OCR via `ocr_service.py` | Tesseract → manual |
| AI document validation | Hosted vision via `ai_document_validator.py` | Heuristic → manual |

## 6. Bonus features
- **Implemented:** Docker + Render deployment; AI document validator.
- **Documented stubs only:** Kafka (dispense events), Ollama (local LLM) — not enabled by
  default; core stability takes priority.

## 7. Acceptance criteria (high level)
- App starts with no credentials; demo users seeded; all role dashboards reachable.
- Admin CRUD works with validation and unique national ID.
- Doctor produces a prescription with a downloadable PDF.
- Pharmacist dispenses and completes the upload→validate→OCR→review→dispense flow.
- Every service falls back cleanly when its key is missing.
- All pages render (no 500s); MVC separation preserved; docs + defense guide present.
