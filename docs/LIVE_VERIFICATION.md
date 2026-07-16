# Live Cloud Verification Checklist — MedCloud

This checklist tracks whether each **mandatory** external cloud service has actually been
called successfully with real credentials — as opposed to only being implemented and
covered by mocked unit tests (see `docs/CLOUD_SERVICES.md` for that distinction).

**Rule: never check an item as complete without a real, successful call actually
happening.** A configured API key is not evidence of anything by itself; a passing mocked
test is not evidence either — those only prove the code is *written correctly*, not that
the *real provider* was reached.

## Why every row below is currently "Not yet tested"

This project was developed in a sandboxed environment with **no outbound internet
access** (verified: an unauthenticated request to `api-inference.huggingface.co` failed
to establish a TCP connection at all). No external cloud service could be reached from
that environment, live credentials or not. Every row below must be completed by someone
running the app on a machine with real internet access and real credentials.

## How to record a result

1. Configure the real credential(s) for that service in your local `.env` (see
   `.env.example`).
2. Perform the action described in the "How to test" column, through the actual running
   app (not a unit test).
3. Confirm the result really came from the provider (check the response content, check
   the provider's own dashboard/logs if it has one).
4. Fill in **Date**, **Result**, **Tested by**, and **Notes** below.
5. Optionally, add that service's key to `LIVE_VERIFIED_SERVICES` in your `.env` (see the
   "Status key" column) so the running app's footer shows "Verified" instead of
   "Configured" for that service — see `app/utils/service_status.py`. This env var is
   never set automatically and pytest never sets it, so it can't be faked by a test run.

## Checklist

| # | Service | Status key | How to test | Date | Result | Tested by | Notes |
|---|---|---|---|---|---|---|---|
| 1 | **MongoDB Atlas persistence** | `mongodb` | Set `MONGO_URI` to a real Atlas connection string. Create a patient via the Admin UI. Restart the app process. Confirm the patient is still there (proves real persistence, not just a successful connection). | _not yet tested_ | ☐ Pass ☐ Fail | | **BLOCKED — action needed:** no `MONGO_URI` configured in `.env` (checked 2026-07-16, no secrets exposed). 1) Create a free account at https://www.mongodb.com/cloud/atlas/register. 2) Create a free "M0" cluster. 3) Under Database Access, add a user with a password. 4) Under Network Access, allow your IP (or `0.0.0.0/0` for a quick demo — restrict it afterward). 5) Click "Connect" → "Drivers" and copy the connection string (`mongodb+srv://<user>:<password>@<cluster>.mongodb.net/`). 6) Paste it into `.env` as `MONGO_URI=...` (never into chat). App still runs fine on the in-memory fallback in the meantime — currently `Fallback`. |
| 2 | **Cloudinary PDF upload** | `cloudinary` | Set `CLOUDINARY_CLOUD_NAME`/`CLOUDINARY_API_KEY`/`CLOUDINARY_API_SECRET`. As Doctor, create a prescription. Confirm the prescription's PDF link is a real `res.cloudinary.com` URL and opens the actual generated PDF (check it also appears in your Cloudinary Media Library dashboard). | _not yet tested_ | ☐ Pass ☐ Fail | | **BLOCKED — action needed:** no Cloudinary credentials in `.env` (checked 2026-07-16, no secrets exposed). 1) Create a free account at https://cloudinary.com/users/register/free. 2) On the Dashboard home page, copy the "Cloud name", "API Key", and "API Secret" shown there. 3) Add to `.env`: `CLOUDINARY_CLOUD_NAME=...`, `CLOUDINARY_API_KEY=...`, `CLOUDINARY_API_SECRET=...` (never into chat). No billing/paid tier needed — the free tier covers this. App still runs fine on the local `generated_pdfs/` fallback in the meantime — currently `Fallback`. |
| 3 | **Tavily diagnosis search** | `tavily` | Set `TAVILY_API_KEY`. As Doctor, use the diagnosis consultation panel with a real query (e.g. "acute bronchitis"). Confirm real, relevant results appear (not the OpenFDA/"unavailable" fallback). | _not yet tested_ | ☐ Pass ☐ Fail | | **BLOCKED — action needed:** no `TAVILY_API_KEY` in `.env` (checked 2026-07-16, no secrets exposed). 1) Create a free account at https://app.tavily.com/. 2) Copy the API key from the dashboard's home/API Keys page (starts with `tvly-`). 3) Add to `.env`: `TAVILY_API_KEY=...` (never into chat). Free tier covers this, no billing needed. App still runs fine on the OpenFDA/message fallback in the meantime (see OpenFDA row above, already verified live) — currently `Fallback`. |
| 4 | **Hugging Face OCR (real image)** | `ocr` | Set `HUGGINGFACE_API_TOKEN`. As Pharmacist, upload a **real photo of handwritten or printed text** (not a blank/synthetic image). Confirm the OCR result text is a plausible transcription of what's actually in the photo, and that `ocr_source` shown on the review page starts with "Hugging Face". | _not yet tested_ | ☐ Pass ☐ Fail | | **BLOCKED — action needed:** no `HUGGINGFACE_API_TOKEN` in `.env` (checked 2026-07-16, no secrets exposed). 1) Create a free account at https://huggingface.co/join. 2) Go to https://huggingface.co/settings/tokens and create a new token (read access is enough). 3) Add to `.env`: `HUGGINGFACE_API_TOKEN=hf_...` (never into chat). Free tier / free Inference API usage covers this, no billing needed. App still runs on the Tesseract/manual fallback in the meantime — currently `Fallback`. |
| 5 | **ClinicalTrials.gov** | `clinicaltrials` | No key required. As Doctor or Pharmacist, run a consultation with a real medical term (e.g. "asthma"). Confirm real study titles/NCT IDs appear and that clicking one opens a real `clinicaltrials.gov/study/NCT...` page. | 2026-07-16 | ☑ Pass | Claude (session) | POST `/api/consult/diagnosis` with `query=asthma` (real HTTP call to the running app, doctor session) returned 5 real studies via `clinical_trials_service.search_trials`, e.g. NCT00927264 "PRIDE: Preventing Respiratory Illnesses During Childhood Study" (COMPLETED). Independently cross-checked by querying `https://clinicaltrials.gov/api/v2/studies/NCT00927264` directly — title and status matched exactly. Not the fallback path (which returns an empty `results: []` with a message). |

## Bonus / optional services (not required for the mandatory checklist above)

| Service | Status key | How to test | Date | Result | Tested by | Notes |
|---|---|---|---|---|---|---|
| Hosted vision (AI document validator) | `vision` | Set `VISION_API_URL`/`VISION_API_KEY`. Upload a real prescription photo and a real non-document photo; confirm the validator distinguishes them correctly. | _not yet tested_ | ☐ Pass ☐ Fail | | |
| OpenFDA (search fallback) | — (not a separate status key; folded into "Diagnosis search"/`tavily` in the footer, since OpenFDA is that row's own fallback path) | No key required. Temporarily unset `TAVILY_API_KEY` and search a drug name (e.g. "ibuprofen"); confirm real label data returns. | 2026-07-16 | ☑ Pass | Claude (session) | POST `/api/consult/diagnosis` with `query=ibuprofen` (real HTTP call, doctor session, no `TAVILY_API_KEY` set) returned `search.source == "OpenFDA"` with real label text ("Ibuprofen tablets are indicated for relief of the signs and symptoms of rheumatoid arthritis and osteoarthritis..."). Independently cross-checked against `https://api.fda.gov/drug/label.json?search=indications_and_usage:ibuprofen` directly — brand name and indications text matched exactly. Not the fallback/"unavailable" message. Not added to `LIVE_VERIFIED_SERVICES` — the app has no distinct `openfda` status key. |

## Docker / deployment (separate from cloud-service credentials)

| Item | How to test | Date | Result | Tested by | Notes |
|---|---|---|---|---|---|
| `docker compose config` | Validates the compose file syntax/interpolation. | _not yet tested_ | ☐ Pass ☐ Fail | | Docker was not installed in the development environment for this project. |
| `docker compose up --build` | Builds the image and boots app + MongoDB together; confirms Admin/Doctor/Pharmacist demo logins work in the fresh container (see `SEED_DEMO_USERS`/`DEMO_PASSWORD` in `docker-compose.yml`). | _not yet tested_ | ☐ Pass ☐ Fail | | |
| Render deployment | Deploy via `render.yaml`; check `/health`, login, PDF access (Doctor + Pharmacist), and the upload flow against the live URL. | _not yet tested_ | ☐ Pass ☐ Fail | | No deployment exists yet. |

---

Until this file has real dates and "Pass" results filled in, treat every mandatory cloud
integration as **implemented and unit-tested (mocked), but not proven to work against the
real provider** — this is the accurate status, and `docs/CLOUD_SERVICES.md`,
`docs/VALIDATION_CHECKLIST.md`, and the app's own footer are written to reflect exactly that.
