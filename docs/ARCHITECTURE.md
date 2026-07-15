# Architecture — MedCloud

## 1. High-level picture
MedCloud is a **Flask/Python** web application following an **MVC-inspired** structure,
consuming several **cloud services** through their APIs. It is a mostly **monolithic**
application (one deployable unit) that talks to **distributed** external services
(MongoDB Atlas, Cloudinary, Tavily, ClinicalTrials.gov, OCR/vision endpoints).

```
        Browser (HTML/CSS/JS)
              │  HTTP (GET/POST)  + JSON (REST) for /api/*
              ▼
        Flask Controllers (blueprints)      ← app/controllers/
              │ call
              ▼
        Services (business logic + API wrappers)   ← app/services/
              │ call                     │ call external cloud APIs
              ▼                          ▼
        Models (MongoDB documents)   Cloud services: MongoDB Atlas, Cloudinary,
              │                       Tavily, OpenFDA, ClinicalTrials.gov, OCR, Vision
              ▼
        Views (Jinja2 templates)     ← app/templates/  (returned to the browser)
```

## 2. MVC mapping (exactly where each part lives)
- **Model** — `app/models/*`: data entities and MongoDB persistence (User, Patient, Visit,
  Prescription, PrescriptionItem, UploadedPrescription, ServiceQueryLog).
- **View** — `app/templates/*`: Jinja2 HTML pages shown to the user.
- **Controller** — `app/controllers/*`: Flask blueprints/routes. They receive the request,
  validate input (WTForms), call services/models, and return a template or redirect.
- **Services** — `app/services/*`: business logic and **all** external cloud API calls.
- **Static** — `app/static/*`: CSS/JS/images. These are **not** views — they are static
  assets served as-is, not rendered per request.

> Rule enforced across the codebase: **controllers never call external APIs directly.**
> They call a service; the service calls the API and handles fallbacks.

## 3. Application factory & composition root
`app/__init__.py::create_app()` is the composition root:
1. loads `Config` (env vars),
2. ensures runtime dirs,
3. initialises the database (`database_service.init_db`) — Atlas or in-memory fallback,
4. seeds demo users on first run,
5. initialises extensions (Flask-Login, CSRF),
6. registers blueprints, error handlers and template context processors.

Entry point `run.py` exposes `app` for the dev server and for gunicorn (`run:app`).

## 4. How Flask connects to cloud services
Each integration is a thin wrapper in `app/services/`:
- `database_service` → MongoDB Atlas (pymongo) or mongomock.
- `cloud_storage_service` → Cloudinary SDK.
- `search_service` → Tavily (HTTP) / OpenFDA (HTTP).
- `clinical_trials_service` → ClinicalTrials.gov REST API v2 (HTTP).
- `ocr_service` → cloud OCR endpoint (HTTP) / local Tesseract.
- `ai_document_validator` → hosted vision endpoint (HTTP) / local Pillow heuristics.

Credentials come only from environment variables (`app/config.py`). If a key is missing the
wrapper switches to its fallback, so the system keeps working.

## 5. Monolithic vs distributed (for the defense)
- The **application** is relatively **monolithic**: the UI layer, the controllers, the
  business logic and the data-access code live in one Flask app and deploy as one unit.
- The **overall system** is **distributed**: the app is one node that communicates over the
  network with separate services (database, storage, search, clinical trials). `docker-compose`
  even runs the app and MongoDB as two separate containers — a small multi-tier setup.
- N-Tiers view: presentation (templates) → application/logic (controllers + services) →
  data (models + MongoDB). Tiers are a logical split by responsibility, not just "more machines".

## 6. Request lifecycle example (create prescription)
1. Doctor submits the prescription form → `POST /doctor/visits/<id>/prescription`.
2. `doctor_controller.new_prescription` validates input and builds items.
3. It calls `prescription_service.create_prescription`, which:
   - persists the `Prescription` (Model → MongoDB),
   - calls `pdf_service` to render the PDF,
   - calls `cloud_storage_service` to store it (Cloudinary or local),
   - saves the PDF location back on the document.
4. Controller redirects to the prescription detail **View** (Jinja2 template).

## 7. Folder structure
See `README.md` → "Project layout". Summary:
`app/{controllers,models,services,forms,utils,templates,static}`, `scripts/`, `docs/`,
`Dockerfile`, `docker-compose.yml`, `render.yaml`, `run.py`.

## 8. Scaling notes
- **Horizontal scaling:** run more gunicorn workers / more app containers behind a load
  balancer (the app is stateless apart from the session cookie and the shared database).
- **Vertical scaling:** give the container more CPU/RAM.
- MongoDB Atlas and Cloudinary scale independently as managed cloud services.
