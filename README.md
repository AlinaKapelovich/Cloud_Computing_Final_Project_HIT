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

1. **Admin** logs in → creates a patient (national ID, name, gender, birth date, etc.) →
   can search the patient list by name/national ID.
2. **Doctor** logs in → selects the patient → records a visit (complaints, diagnosis) →
   optionally **consults** Tavily + ClinicalTrials.gov (Doctor-only) → creates a
   prescription with medications → a **PDF is generated** and stored (Cloudinary, or
   local fallback, openable by both Doctor and Pharmacist).
3. **Pharmacist** logs in → can **consult drug side-effects** (Pharmacist-only) right
   away, without needing to find a patient first → searches a patient by national ID and
   sees the actual medications on each prescription → **dispenses** the open prescription
   → uploads a **handwritten** prescription image → the app runs **AI document
   validation → OCR (image-to-text) → review**. If the image is flagged invalid,
   dispensing is blocked; if validation is unavailable, dispensing requires an explicit
   "I manually confirm this is a prescription document" checkbox → dispenses the
   uploaded prescription.

---

## Tests

```bash
python -m pytest        # 78 tests, no credentials needed, zero real network/Tesseract calls
```

The suite drives the real flows through Flask's test client: auth/roles, patient CRUD
(including search), visit→prescription→PDF, RBAC on the consultation endpoints, mocked
provider tests (Hugging Face OCR, Tavily, OpenFDA, ClinicalTrials.gov, Cloudinary), the
AI-validator dispense-enforcement states, service-status accuracy, demo-user seeding
policy, and the pharmacist upload→AI validation→OCR→review→dispense flow, plus a render
sweep of every page for every role.

`tests/conftest.py::block_real_network` replaces `requests.post`/`requests.get`, and
`::block_real_tesseract` replaces the real Tesseract call, each with a stub unless a test
explicitly opts out — so the standard suite never makes a real outbound call or invokes
the real Tesseract binary, even on a machine with internet access, real API keys, and
Tesseract installed. A genuine real-Tesseract check exists as an opt-in integration test:

```bash
python -m pytest -m integration   # runs only the real-Tesseract check; skips itself if not installed
```

---

## Running with Docker

```bash
docker compose up --build
# open http://localhost:5000  (MongoDB runs in a second container; data persists)
```

`docker-compose.yml` points the app at a real MongoDB container (`MONGO_URI` is set), so
demo-user auto-seeding would normally be skipped (see "Demo user seeding" above) — leaving
a fresh container with no working login. To keep the demo usable, compose explicitly sets
`SEED_DEMO_USERS: "true"` and `DEMO_PASSWORD: "demo1234"`, so `admin@/doctor@/pharmacist@example.com`
work immediately on a fresh container. Never do this against a real production database.

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

> ⚠️ **Not yet deployed.** No live Render URL exists for this project. The steps below
> describe how to deploy it; do not claim a working deployment until you've actually
> created one and checked `/health`, login, PDF access, and the upload flow against it.

1. Push this repository to GitHub.
2. On [render.com](https://render.com) create a new **Blueprint** and point it at the repo
   (it reads [`render.yaml`](render.yaml)).
3. Render builds the Docker image and runs it. `SECRET_KEY` is generated automatically;
   set `MONGO_URI` and any cloud keys in the dashboard to enable the real integrations.
   Set `SEED_DEMO_USERS=true` explicitly if you want the demo1234 accounts available on a
   real database for the defense — it is never enabled silently (see Configuration below).
4. Health check path is `/health`.

---

## Configuration

Copy `.env.example` to `.env` and fill in what you have. **Anything left empty uses a
fallback**, so the app always runs.

| Variable | Enables | Fallback if empty |
|---|---|---|
| `MONGO_URI` | MongoDB Atlas (cloud DB) | In-memory demo DB (mongomock) |
| `SEED_DEMO_USERS` | Force demo-user seeding on/off | Auto: seeds only when `MONGO_URI` is empty (demo mode) |
| `DEMO_PASSWORD` | Password for seeded demo accounts | `demo1234` |
| `CLOUDINARY_*` | PDF cloud storage | Local `generated_pdfs/` |
| `TAVILY_API_KEY` | Diagnosis web search | OpenFDA, then a clear message |
| `HUGGINGFACE_API_TOKEN` / `HUGGINGFACE_OCR_MODEL` | Cloud OCR (Hugging Face TrOCR) | Generic `OCR_API_URL`, then Tesseract, then manual transcription |
| `OCR_API_URL` / `OCR_API_KEY` | Generic cloud OCR (alternate provider) | Tesseract, then manual transcription |
| `VISION_API_URL` / `VISION_API_KEY` | AI document validation | Local heuristic checks, then required manual confirmation |
| `CLINICAL_TRIALS_BASE_URL` | ClinicalTrials.gov | Public API (no key needed) |
| `FLASK_DEBUG` | Auto-reload + interactive debugger | **Off by default** — a fresh clone is production-safe |

Secrets are **never** hardcoded or committed. `.env` is git-ignored. `SEED_DEMO_USERS`
is never silently enabled against a real, persistent database (`MONGO_URI` set) — see
`docs/CLOUD_SERVICES.md` and `app/services/bootstrap.py`.

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
scripts/build_submission_zip.py  Package a clean submission archive (see below)
docs/                      PRD, ARCHITECTURE, USER_FLOWS, DATA_MODEL, CLOUD_SERVICES,
                           UI_UX_PLAN, IMPLEMENTATION_ROADMAP, VALIDATION_CHECKLIST,
                           DEFENSE_GUIDE, LIVE_VERIFICATION
Dockerfile, docker-compose.yml, render.yaml
```

---

## Packaging a submission

```bash
python scripts/build_submission_zip.py
# or specify an output path: python scripts/build_submission_zip.py my_submission.zip
```

Builds a ZIP containing only `app/`, `docs/`, `tests/`, `scripts/`, and configuration
templates (`requirements.txt`, `.env.example`, `Dockerfile`, etc.). Excludes `.git`,
`.env`, `uploads/`, `generated_pdfs/`, `__pycache__`, `.pytest_cache`, virtual
environments, and the course-material/lecture-transcript folders — and verifies none of
them ended up in the archive before reporting success.

---

## Documentation

Full planning and defense material is in [`docs/`](docs/), most importantly
[`docs/DEFENSE_GUIDE.md`](docs/DEFENSE_GUIDE.md) — short oral answers for every concept the
examiner asks (cloud computing, MVC, HTTP vs REST, API, Docker, MongoDB/NoSQL, scaling,
monolithic vs distributed, Data Lake vs Database, etc.) and how to explain any code file.

[`docs/CLOUD_SERVICES.md`](docs/CLOUD_SERVICES.md) documents what's *implemented* (and
mocked-tested) for each cloud integration; [`docs/LIVE_VERIFICATION.md`](docs/LIVE_VERIFICATION.md)
is the separate checklist for what's actually been *proven to work live* — currently
every row is "not yet tested" (no outbound internet in the development environment).
Complete it yourself with real credentials before claiming any provider works live.

---

## Bonus / future extensions

- **Docker + Render** — configuration written (`Dockerfile`, `docker-compose.yml`,
  `render.yaml`) but **not build-verified**: Docker was not installed in this development
  environment, and no Render deployment has been created yet. Run `docker compose config`
  / `docker compose up --build` yourself before relying on this for the defense.
- **AI document validator** — implemented, including real dispense-time enforcement
  (blocks on an invalid document; requires explicit manual confirmation when validation
  is unavailable) — not hosted-vision-tested live, but fully covered by mocked/heuristic tests.
- **Kafka** (dispense events) and **Ollama** (local LLM) — documented **stubs only**; not
  enabled by default so the core system stays stable and easy to defend.
