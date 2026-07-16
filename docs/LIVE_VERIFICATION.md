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
| 1 | **MongoDB Atlas persistence** | `mongodb` | Set `MONGO_URI` to a real Atlas connection string. Create a patient via the Admin UI. Restart the app process. Confirm the patient is still there (proves real persistence, not just a successful connection). | _not yet tested_ | ☐ Pass ☐ Fail | | |
| 2 | **Cloudinary PDF upload** | `cloudinary` | Set `CLOUDINARY_CLOUD_NAME`/`CLOUDINARY_API_KEY`/`CLOUDINARY_API_SECRET`. As Doctor, create a prescription. Confirm the prescription's PDF link is a real `res.cloudinary.com` URL and opens the actual generated PDF (check it also appears in your Cloudinary Media Library dashboard). | _not yet tested_ | ☐ Pass ☐ Fail | | |
| 3 | **Tavily diagnosis search** | `tavily` | Set `TAVILY_API_KEY`. As Doctor, use the diagnosis consultation panel with a real query (e.g. "acute bronchitis"). Confirm real, relevant results appear (not the OpenFDA/"unavailable" fallback). | _not yet tested_ | ☐ Pass ☐ Fail | | |
| 4 | **Hugging Face OCR (real image)** | `ocr` | Set `HUGGINGFACE_API_TOKEN`. As Pharmacist, upload a **real photo of handwritten or printed text** (not a blank/synthetic image). Confirm the OCR result text is a plausible transcription of what's actually in the photo, and that `ocr_source` shown on the review page starts with "Hugging Face". | _not yet tested_ | ☐ Pass ☐ Fail | | |
| 5 | **ClinicalTrials.gov** | `clinicaltrials` | No key required. As Doctor or Pharmacist, run a consultation with a real medical term (e.g. "asthma"). Confirm real study titles/NCT IDs appear and that clicking one opens a real `clinicaltrials.gov/study/NCT...` page. | _not yet tested_ | ☐ Pass ☐ Fail | | |

## Bonus / optional services (not required for the mandatory checklist above)

| Service | Status key | How to test | Date | Result | Tested by | Notes |
|---|---|---|---|---|---|---|
| Hosted vision (AI document validator) | `vision` | Set `VISION_API_URL`/`VISION_API_KEY`. Upload a real prescription photo and a real non-document photo; confirm the validator distinguishes them correctly. | _not yet tested_ | ☐ Pass ☐ Fail | | |
| OpenFDA (search fallback) | — | No key required. Temporarily unset `TAVILY_API_KEY` and search a drug name (e.g. "ibuprofen"); confirm real label data returns. | _not yet tested_ | ☐ Pass ☐ Fail | | |

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
