# Cloud Services — MedCloud

Every external service is isolated behind a wrapper in `app/services/`. Controllers never
call these APIs directly. Each wrapper handles: missing key, timeout, invalid response,
empty result, service unavailable — always degrading to a documented fallback.

---

## 1. cloud_storage_service.py — Cloudinary (PDF storage)
- **Purpose:** upload the generated prescription PDF and return a public URL stored in Mongo.
- **Provider:** Cloudinary (object/blob storage — Storage-as-a-Service).
- **Env vars:** `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
- **Input:** local PDF path + a public id. **Output:** `{storage, url, path}`.
- **Failure cases:** missing keys, upload error/timeout.
- **Fallback:** keep the PDF locally under `generated_pdfs/` and serve it via
  `doctor.prescription_pdf_file`. `pdf_storage` records which backend was used.
- **Defense:** demonstrates consuming a managed cloud storage service via its API/SDK.

## 2. database_service.py — MongoDB Atlas (cloud NoSQL)
- **Purpose:** provide the app's database handle.
- **Provider:** MongoDB Atlas (Database-as-a-Service). **Env:** `MONGO_URI`, `MONGO_DB_NAME`.
- **Failure cases:** no URI, unreachable cluster, auth failure (ping checked at startup).
- **Fallback:** in-memory `mongomock` database so the app runs with zero credentials.
- **Defense:** NoSQL/MongoDB (Database → Collections → Documents); managed DB service.

## 3. search_service.py — Tavily (+ OpenFDA fallback)
- **Purpose:** diagnosis/drug consultation via real-time cloud search.
- **Provider:** Tavily (primary). **Env:** `TAVILY_API_KEY`.
- **Fallback chain:** Tavily → **OpenFDA** drug label API (keyless) for drug-related queries →
  clear "service disabled" message.
- **Input:** query string. **Output:** `{source, message, results:[{title,snippet,url}]}`.
- **Defense:** consuming a third-party REST API; graceful multi-level fallback.

## 4. clinical_trials_service.py — ClinicalTrials.gov (official requirement)
- **Purpose:** clinical research related to a diagnosis/treatment/side-effect.
- **Provider:** ClinicalTrials.gov public REST API v2 (no key). **Env:** `CLINICAL_TRIALS_BASE_URL`.
- **Input:** query. **Output:** `{source, message, results:[{nct_id,title,status,url}]}`.
- **Failure/empty:** returns an **empty but valid** structure with a message — never raises.
- **Defense:** a keyless public REST API used alongside Tavily; complements (not replaced by) OpenFDA.

## 5. ocr_service.py — Cloud OCR (+ Tesseract + manual)
- **Purpose:** extract text from a handwritten/scanned prescription image.
- **Provider:** cloud OCR endpoint (e.g. HuggingFace / PaddleOCR-VL). **Env:** `OCR_API_URL`, `OCR_API_KEY`.
- **Fallback chain:** Cloud OCR → local **Tesseract** (installed in the Docker image) → **manual**
  transcription message. Runs **after** AI document validation.
- **Input:** image path. **Output:** `{text, source, message}`. Result stored on the upload.
- **Defense:** cloud-first design with resilient local/manual fallbacks.

## 6. ai_document_validator.py — Hosted vision (+ heuristic) [bonus]
- **Purpose:** verify an upload looks like a real prescription/document **before** OCR.
- **Provider:** hosted vision model. **Env:** `VISION_API_URL`, `VISION_API_KEY`.
- **Fallback:** local Pillow **heuristics** (type, size, dimensions, aspect, not-empty/corrupt);
  if impossible, mark "unavailable — manual confirmation".
- **Output:** `{valid, method, message, details}` stored on the upload and shown in the UI.
- **Defense:** AI-as-a-service with an always-working offline fallback.

## 7. kafka_service.py — dispense events [future stub]
- **Purpose:** publish a `prescription.dispensed` event for downstream systems.
- **Env:** `KAFKA_ENABLED`, `KAFKA_BOOTSTRAP_SERVERS`.
- **Fallback (default):** log the event to the console; no hard Kafka dependency.
- **Defense:** Kafka = event/message routing between systems (distributed, asynchronous).

## 8. ollama_service — local LLM [future, documented only]
- **Purpose:** optional local LLM assistance. **Env:** `OLLAMA_ENABLED`, `OLLAMA_BASE_URL`.
- **Status:** not implemented beyond documentation; enabled only after core stability.

---

## Central rules
- Controllers call services; services call APIs. Secrets only from env vars (`config.py`).
- The footer status strip and `service_status.py` show, live, which services are **real** vs
  **fallback**, so it's transparent during the defense.
