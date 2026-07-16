# Cloud Services — MedCloud

Every external service is isolated behind a wrapper in `app/services/`. Controllers never
call these APIs directly. Each wrapper handles: missing key, timeout, invalid response,
empty result, service unavailable — always degrading to a documented fallback.

To actually perform and record a real live test for a mandatory service, see
[`docs/LIVE_VERIFICATION.md`](LIVE_VERIFICATION.md) — this document describes what's
*implemented*, that one tracks what's *proven to work live*.

## Status legend (used consistently below)
- **Mandatory — implemented and tested (mocked).** Real request/response handling is
  written against the provider's documented contract and is exercised by a pytest test
  that mocks `requests.post`/`requests.get` with a realistic response. It has **not**
  been exercised against the live provider with a real credential (see "Live-testing
  note" below) — the fallback path is what actually runs whenever you use the app
  without a key, including in this repository's own demo.
- **Mandatory — implemented with fallback, live credentials still required.** Same as
  above, plus: this is one of the project brief's mandatory cloud integrations.
- **Bonus — implemented.** An official bonus feature with working code and tests.
- **Bonus — configured but unverified.** Wiring exists (env vars, service file) but the
  feature has not been exercised at all, live or mocked.
- **Future-only.** Documented stub, not part of the working system, disabled by default.

### Live-testing note
This project was developed in a sandboxed environment **with no outbound internet
access** (confirmed: an unauthenticated request to `api-inference.huggingface.co`
failed to connect at the TCP level). That means **no external cloud service in this
project — MongoDB Atlas, Cloudinary, Tavily, Hugging Face, OpenFDA, ClinicalTrials.gov,
or a hosted vision endpoint — has been tested live with real credentials**, and no such
claim is made anywhere in this documentation. What **is** verified:
1. Every provider's request/response handling is implemented against its real,
   documented API contract (exact URLs, headers, payload shapes, response parsing).
2. Every provider's success path, failure path, and fallback chain is covered by a
   pytest test that mocks the HTTP call (see `tests/test_ocr_provider.py`,
   `tests/test_consultations.py`, `tests/test_cloud_storage.py`).
3. Every service, with **zero** credentials configured, degrades to its documented
   fallback and the application keeps working end-to-end (this is what running the app
   locally right now actually demonstrates).
4. `python -m pytest`'s standard run never makes a real network call — see
   `tests/conftest.py::block_real_network` — so this is true in CI too, not just here.

### Runtime status badge (Fallback / Configured / Verified)
The app's own footer (and `app/utils/service_status.py`) shows a live, three-state badge
per service, computed at runtime, which is a separate (and stricter) thing from the
"Tested live" notes below:
- **Fallback** — no credentials configured; using the documented local fallback.
- **Configured** — credentials ARE present, so a real call will be attempted, but this
  is *not* a claim that one has ever succeeded. A keyless public API (ClinicalTrials.gov)
  is also only ever "Configured", never elevated just for being reachable.
- **Verified** — a human has completed `docs/LIVE_VERIFICATION.md` for that service
  (recorded a real, successful call, with date and result) and added its key to the
  `LIVE_VERIFIED_SERVICES` env var. This is never set automatically by the app, and
  pytest never sets it — a mocked test can never make a service appear "Verified".

**Do not update this document to claim a provider is "tested live" without first
completing the corresponding row in `docs/LIVE_VERIFICATION.md`** — that file, not this
one, is the source of truth for real live-testing results.

---

## 1. database_service.py — MongoDB Atlas (cloud NoSQL)
**Status: Mandatory — implemented with fallback, live credentials still required.**
- **Purpose:** provide the app's database handle.
- **Provider:** MongoDB Atlas (Database-as-a-Service). **Env:** `MONGO_URI`, `MONGO_DB_NAME`.
- **Input:** none (connection only). **Output:** a pymongo `Database` handle.
- **Failure cases:** no URI, unreachable cluster, auth failure (checked with a `ping`
  command at startup).
- **Fallback:** in-memory `mongomock` database so the app runs with zero credentials.
  This is what the demo actually runs on — nothing persists across a restart.
- **Tested live:** No (no MONGO_URI available in this environment). Fallback path is
  exercised by every single test in the suite (52+ tests all run against mongomock).
- **Defense:** NoSQL/MongoDB (Database → Collections → Documents); managed DB service.

## 2. cloud_storage_service.py — Cloudinary (PDF storage)
**Status: Mandatory — implemented with fallback, live credentials still required.**
- **Purpose:** upload the generated prescription PDF and return a public URL stored in Mongo.
- **Provider:** Cloudinary (object/blob storage — Storage-as-a-Service).
- **Env vars:** `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
- **Input:** local PDF path + a public id. **Output:** `{storage, url, path}`.
- **Failure cases:** missing keys, upload error/timeout.
- **Fallback:** keep the PDF locally under `generated_pdfs/` and serve it via the shared
  `main.prescription_pdf_file` route (reachable by both Doctor and Pharmacist — see
  `tests/test_doctor_prescription.py::test_pharmacist_can_open_locally_stored_pdf`).
  `pdf_storage` records which backend was actually used.
- **Tested live:** No. Mocked success test:
  `tests/test_cloud_storage.py::test_pdf_uploads_to_cloudinary_when_configured`
  (monkeypatches `cloudinary.uploader.upload` against the real call signature).
- **Defense:** demonstrates consuming a managed cloud storage service via its SDK.

## 3. search_service.py — Tavily (+ OpenFDA fallback)
**Status: Mandatory — implemented with fallback, live credentials still required.**
- **Purpose:** diagnosis consultation (Doctor) and drug side-effects lookup (Pharmacist)
  via real-time cloud search.
- **Provider:** Tavily (primary). **Env:** `TAVILY_API_KEY`.
- **Fallback chain:** Tavily → **OpenFDA** drug label API (keyless) → clear "search
  disabled" message. OpenFDA supplements Tavily; it does not replace ClinicalTrials.gov.
- **Input:** query string. **Output:** `{source, message, results:[{title,snippet,url}]}`.
- **Tested live:** No. Mocked success tests:
  `test_tavily_success_is_parsed_correctly`, `test_openfda_success_is_parsed_correctly`
  (both in `tests/test_consultations.py`), exercising the real request/response shapes.
- **Access control:** the `/api/consult/diagnosis` endpoint is Doctor-only;
  `/api/consult/side-effects` is Pharmacist-only (enforced server-side, see
  `tests/test_consultation_rbac.py`).
- **Defense:** consuming a third-party REST API; graceful multi-level fallback.

## 4. clinical_trials_service.py — ClinicalTrials.gov (official requirement)
**Status: Mandatory — implemented with fallback, live credentials still required (none needed — keyless API, but not live-network-tested here).**
- **Purpose:** clinical research related to a diagnosis/treatment/side-effect. This is
  an explicit official requirement, not optional, and is not replaceable by OpenFDA.
- **Provider:** ClinicalTrials.gov public REST API v2 (no key). **Env:** `CLINICAL_TRIALS_BASE_URL`.
- **Input:** query. **Output:** `{source, message, results:[{nct_id,title,status,url}]}`.
- **Failure/empty:** returns an **empty but valid** structure with a message — never raises.
- **Tested live:** No (no outbound network in this environment). Mocked success test:
  `test_clinical_trials_success_is_parsed_correctly`; graceful-failure test:
  `test_clinical_trials_service_never_raises` (both in `tests/test_consultations.py`).
- **Defense:** a keyless public REST API used alongside Tavily/OpenFDA for both roles.

## 5. ocr_service.py — Hugging Face (+ generic cloud OCR + Tesseract + manual)
**Status: Mandatory — implemented with fallback, live credentials still required.**
- **Purpose:** extract text from a handwritten/scanned prescription image (image-to-text,
  **not** translation — the source and target language are the same).
- **Primary provider (concrete, implemented):** Hugging Face Inference API running a
  TrOCR handwritten-text model (`microsoft/trocr-base-handwritten` by default).
  **Env:** `HUGGINGFACE_API_TOKEN`, `HUGGINGFACE_OCR_MODEL`.
  Request: `POST https://api-inference.huggingface.co/models/<model>` with
  `Authorization: Bearer <token>` and the raw image bytes as the body. Response: a JSON
  list `[{"generated_text": "..."}]`; a `503` with an `"error"` field means the shared
  model is cold-starting and is treated as a transient failure (falls through the chain).
- **Secondary provider:** a generic `OCR_API_URL`/`OCR_API_KEY` endpoint (escape hatch
  for a different cloud OCR provider), accepting either a JSON `{"text": ...}` or plain
  text response.
- **Fallback chain:** Hugging Face → generic cloud endpoint → local **Tesseract**
  (installed in the Docker image; not installed in this development environment) →
  **manual transcription** by the pharmacist. Runs **after** AI document validation.
- **Input:** image path. **Output:** `{text, source, message}`, stored on the upload and
  shown for pharmacist review/correction before dispensing.
- **Tested live:** No. Mocked tests in `tests/test_ocr_provider.py` cover: Hugging Face
  success, Hugging Face 503 cold-start falling through the chain, Hugging Face failure
  falling back to the generic cloud endpoint, no-provider-configured still returning a
  valid result, and manual text being preserved through to dispensing.
- **Defense:** cloud-first design against one concretely implemented provider, with
  resilient local/manual fallbacks so the pharmacist workflow never breaks.

## 6. ai_document_validator.py — Hosted vision (+ heuristic) [bonus]
**Status: Bonus — implemented.**
- **Purpose:** verify an upload looks like a real prescription/document **before** OCR,
  and gate dispensing on the result.
- **Provider:** hosted vision model. **Env:** `VISION_API_URL`, `VISION_API_KEY`.
- **Fallback:** local Pillow **heuristics** (type, size, dimensions, aspect,
  not-empty/corrupt); if neither can decide, `valid: None` ("unavailable").
- **Enforcement (dispense-time, not just display):**
  - `valid is True` → dispensing proceeds normally.
  - `valid is False` → dispensing is **blocked**; the pharmacist is shown a clear error
    and directed to upload a different image — never dispensed "as if normal".
  - `valid is None` → dispensing is **blocked** until the pharmacist explicitly checks
    "I manually confirm that this image is a prescription document." The confirmation
    (`manual_confirmed`, `manual_confirmed_by`, `manual_confirmed_at`) is stored on the
    upload record.
- **Tested live:** No hosted vision provider tested live (no `VISION_API_URL` available).
  All four enforcement states are covered by `tests/test_ai_validator_enforcement.py`
  (valid / invalid / unavailable-blocked / unavailable-confirmed).
- **Defense:** AI-as-a-service with an always-working offline fallback and a real
  enforcement gate, not a cosmetic status badge.

## 7. kafka_service.py — dispense events
**Status: Future-only.**
- **Purpose:** publish a `prescription.dispensed` event for downstream systems.
- **Env:** `KAFKA_ENABLED`, `KAFKA_BOOTSTRAP_SERVERS`.
- **Current behaviour:** always logs the event to the console; the real producer branch
  raises `NotImplementedError` internally and is caught, so this is a documented stub,
  not a working Kafka integration. Disabled by default; never destabilizes the app.
- **Defense:** Kafka = event/message routing between systems (distributed, asynchronous).

## 8. ollama_service — local LLM
**Status: Future-only.**
- **Purpose:** optional local LLM assistance. **Env:** `OLLAMA_ENABLED`, `OLLAMA_BASE_URL`.
- **Current behaviour:** not implemented — no service file exists. Documented as a
  possible future extension only, per the project's explicit priority (core stability
  first). Not wired into any route or template.

---

## Central rules
- Controllers call services; services call APIs. Secrets only from env vars (`config.py`).
- The footer status strip and `service_status.py` show, live, which services are **real**
  (credentials configured) vs **fallback** (no credentials) — this reflects the actual
  runtime state, not a claim about whether the provider was ever tested live.
- The standard `python -m pytest` run makes zero real network calls (see
  `tests/conftest.py::block_real_network`), so test results are deterministic regardless
  of whether the machine running them has internet access.
