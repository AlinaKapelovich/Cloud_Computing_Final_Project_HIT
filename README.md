# MedCloud — Cloud Prescription Management

A medical prescription management web application built for the HIT **Cloud Computing**
final project (course 43008). It demonstrates cloud computing concepts, a clean
**MVC** architecture in **Flask/Python**, consumption of cloud services through APIs,
and the **PIV** methodology (Planning → Implementation → Validation).

Three roles: **Admin**, **Doctor**, **Pharmacist**.

---

## Quick start (local, zero credentials)

```bash
pip install -r requirements.txt
python run.py
# open http://localhost:5000
```

The app runs immediately with **no cloud credentials**: it uses an in-memory database
(mongomock) and every external service degrades to a documented fallback. Demo users are
seeded automatically.

### Demo accounts (password `demo1234`)

| Role       | Email                     |
|------------|---------------------------|
| Admin      | `admin@example.com`       |
| Doctor     | `doctor@example.com`      |
| Pharmacist | `pharmacist@example.com`  |

> The demo password comes from the `DEMO_PASSWORD` env var (default `demo1234`) — it is
> not a real secret and is only used to seed demo accounts.

---

## Demo flow (for the defense)

1. **Admin** logs in → creates a patient (national ID, name, gender, birth date, etc.).
2. **Doctor** logs in → selects the patient → records a visit (complaints, diagnosis) →
   optionally **consults** Tavily + ClinicalTrials.gov → creates a prescription with
   medications → a **PDF is generated** and stored (Cloudinary, or local fallback).
3. **Pharmacist** logs in → searches the patient by national ID → **dispenses** the open
   prescription → uploads a **handwritten** prescription image → the app runs
   **AI document validation → OCR → review** → dispenses the uploaded prescription →
   can **consult drug side-effects**.

---

## Tests

```bash
python -m pytest        # 43 tests, no credentials needed
```

The suite drives the real flows through Flask's test client: auth/roles, patient CRUD,
visit→prescription→PDF, consultation fallbacks, and the pharmacist upload→AI validation→OCR→
dispense flow, plus a render sweep of every page for every role.

---

## Running with Docker

```bash
docker compose up --build
# open http://localhost:5000  (MongoDB runs in a second container; data persists)
```

Or just the app image:

```bash
docker build -t medcloud .
docker run -p 5000:5000 medcloud
```

The Docker image also installs **Tesseract**, so the local OCR fallback works inside the
container even without a cloud OCR key.

> ⚠️ **Known limitation:** the Docker image has **not been built/executed yet** — Docker was
> not installed on the machine where this project was developed. The `Dockerfile`,
> `docker-compose.yml` and `render.yaml` follow standard practice but are **unverified**.
> Run `docker compose config` and `docker compose up --build` on a machine with Docker
> before relying on them for the defense.

---

## Deploying to Render

1. Push this repository to GitHub.
2. On [render.com](https://render.com) create a new **Blueprint** and point it at the repo
   (it reads [`render.yaml`](render.yaml)).
3. Render builds the Docker image and runs it. `SECRET_KEY` is generated automatically;
   set `MONGO_URI` and any cloud keys in the dashboard to enable the real integrations.
4. Health check path is `/health`.

---

## Configuration

Copy `.env.example` to `.env` and fill in what you have. **Anything left empty uses a
fallback**, so the app always runs.

| Variable | Enables | Fallback if empty |
|---|---|---|
| `MONGO_URI` | MongoDB Atlas (cloud DB) | In-memory demo DB (mongomock) |
| `CLOUDINARY_*` | PDF cloud storage | Local `generated_pdfs/` |
| `TAVILY_API_KEY` | Diagnosis web search | OpenFDA, then a clear message |
| `OCR_API_URL` / `OCR_API_KEY` | Cloud OCR | Tesseract, then manual transcription |
| `VISION_API_URL` / `VISION_API_KEY` | AI document validation | Local heuristic checks |
| `CLINICAL_TRIALS_BASE_URL` | ClinicalTrials.gov | Public API (no key needed) |

Secrets are **never** hardcoded or committed. `.env` is git-ignored.

---

## Architecture (MVC + services)

```
Controllers  app/controllers/  Flask blueprints (thin: validate + delegate)
Views        app/templates/    Jinja2 HTML pages
Models       app/models/       Data entities + MongoDB persistence
Services     app/services/     Business logic + external cloud API wrappers
Static       app/static/       CSS / JS / images (not views)
```

Controllers never call external APIs directly — every integration lives behind a service
wrapper with a fallback. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

### Project layout

```
run.py                     App entry point (gunicorn: run:app)
app/__init__.py            Application factory (composition root)
app/config.py              Environment-based configuration
app/controllers/           auth, admin, doctor, pharmacist, api, main
app/models/                user, patient, visit, prescription, prescription_item,
                           uploaded_prescription, service_query_log
app/services/              database, patient, prescription, pdf, cloud_storage, ocr,
                           search, clinical_trials, ai_document_validator,
                           kafka (future stub), bootstrap
app/forms/                 WTForms (validation + CSRF)
app/templates/, app/static/
scripts/seed_users.py      Seed demo users into a real Atlas DB
docs/                      PRD, ARCHITECTURE, USER_FLOWS, DATA_MODEL, CLOUD_SERVICES,
                           UI_UX_PLAN, IMPLEMENTATION_ROADMAP, VALIDATION_CHECKLIST,
                           DEFENSE_GUIDE
Dockerfile, docker-compose.yml, render.yaml
```

---

## Documentation

Full planning and defense material is in [`docs/`](docs/), most importantly
[`docs/DEFENSE_GUIDE.md`](docs/DEFENSE_GUIDE.md) — short oral answers for every concept the
examiner asks (cloud computing, MVC, HTTP vs REST, API, Docker, MongoDB/NoSQL, scaling,
monolithic vs distributed, Data Lake vs Database, etc.) and how to explain any code file.

---

## Bonus / future extensions

- **Docker + Render** — implemented (this repo).
- **AI document validator** — implemented (hosted vision + heuristic fallback).
- **Kafka** (dispense events) and **Ollama** (local LLM) — documented **stubs only**; not
  enabled by default so the core system stays stable and easy to defend.
