# Implementation Roadmap — MedCloud

Built milestone-by-milestone with a self-validating loop (implement → validate → fix →
re-validate). Status reflects the delivered app.

| # | Milestone | Key files | Acceptance / validation | Status |
|---|-----------|-----------|-------------------------|--------|
| M0 | Docs + skeleton | `docs/*`, `app/` structure | 10 docs exist; app package imports | ✅ |
| M1 | Flask foundation | `app/__init__.py`, `config.py`, `extensions.py`, `run.py`, `database_service.py`, base template, error pages, `/health` | App starts; `/health` 200; DB fallback works | ✅ |
| M2 | Auth & roles | `models/user.py`, `auth_controller.py`, `utils/decorators.py`, `bootstrap.py`, `scripts/seed_users.py` | Hashed login; RBAC; demo users; role isolation (403) | ✅ |
| M3 | Admin patients | `models/patient.py`, `patient_service.py`, `forms/patient_forms.py`, `admin_controller.py`, admin templates | CRUD; unique national ID; calculated age; validation | ✅ |
| M4 | Doctor prescription + PDF | `models/{visit,prescription,prescription_item}.py`, `pdf_service.py`, `cloud_storage_service.py`, `prescription_service.py`, doctor templates | Visit→prescription→PDF; local/Cloudinary storage | ✅ |
| M5 | Consultations | `search_service.py`, `clinical_trials_service.py`, `models/service_query_log.py`, `api_controller.py`, `consult.js` | Valid JSON + graceful fallback offline; queries logged | ✅ |
| M6 | Pharmacist flow | `models/uploaded_prescription.py`, `forms/upload_forms.py`, `pharmacist_controller.py`, pharmacist templates | Search, dispense, upload→review→dispense | ✅ |
| M7 | AI document validator | `ai_document_validator.py`, `ocr_service.py`, `kafka_service.py` | Validate-before-OCR; heuristic + manual fallbacks | ✅ |
| M8 | UI/UX polish | `static/css/styles.css`, shared macros | All pages render (no 500s); consistent design | ✅ |
| M9 | Docker + deploy | `Dockerfile`, `docker-compose.yml`, `render.yaml`, `README.md`, `.env.example`, `.dockerignore` | Image builds; compose runs app+mongo; Render blueprint | ⚠️ config written; **build NOT verified** — Docker is not installed in this development environment (no `docker` binary, no Docker Desktop process). Run `docker compose config` and `docker compose up --build` yourself before the defense. |
| M10 | Final validation | smoke tests, this doc set | Requirements ↔ code ↔ docs cross-check; no secrets | ✅ |
| M11 | Requirements-completion pass | RBAC on consult API, AI-validator dispense enforcement, one concrete OCR provider (Hugging Face), Admin patient search, pharmacist medication visibility, always-reachable side-effects consult, `SEED_DEMO_USERS`/`FLASK_DEBUG` production defaults, network-blocked deterministic test suite, removal of the ungrounded "Clinical workflow" card and "Staff accounts" stat | Full pytest suite green with zero real network calls; every claim in this doc set checked against what the code actually does | ✅ |

## Validation approach
- `python -m compileall app` after each change.
- Per-milestone smoke tests via Flask's test client (auth, CRUD, prescription+PDF,
  consultation structure, pharmacist upload flow) + a full route-render sweep across all roles.

## Ordering principle
Core Admin/Doctor/Pharmacist flows first; bonuses (Docker, AI validator) after core is stable;
Kafka/Ollama kept as documented stubs only.
