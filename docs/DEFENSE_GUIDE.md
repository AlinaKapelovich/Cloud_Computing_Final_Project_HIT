# Defense Guide — MedCloud

Short, oral-ready answers (English) for every concept the examiner asks, each tied to where
it appears in this project. Grounded in the course concept sheet and the questions the
instructor has actually asked (explain a random code file + concept questions + UI/UX).

---

## What the project does (30-second pitch)
MedCloud is a cloud-based prescription management system with three roles. An **admin**
manages patients, a **doctor** records visits and writes prescriptions (generating a PDF
stored in the cloud), and a **pharmacist** dispenses prescriptions and digitises handwritten
ones with OCR. It is built in Flask with clean MVC and consumes several cloud services, each
with a safe fallback so it always runs.

---

## Core concepts

**1. Monolithic system.** Most of the app (UI, logic, data access) is one deployable unit.
Simple to build and run; harder to scale a single part independently. *Here:* our Flask app
is relatively monolithic, but it consumes external cloud services.

**2. Distributed / N-Tiers.** A system split into components/tiers by responsibility that
talk over a network. N-Tiers = presentation / logic / data. *Here:* app ↔ MongoDB ↔ storage
↔ search are separate services; `docker-compose` runs app + MongoDB as two containers.

**3. Cloud computing.** Using computing resources over the internet, on demand, instead of
owning all the infrastructure. **Two reasons to use it:** (1) elasticity/scaling on demand,
(2) no need to buy/maintain your own servers (pay-as-you-go, high availability). *Here:*
Atlas, Cloudinary, Tavily, ClinicalTrials.gov.

**4. Cloud service.** A computing capability delivered over the internet (storage, database,
OCR, AI, an API). *Here:* every wrapper in `app/services/`.

**5. IaaS / PaaS / SaaS / XaaS.** Infrastructure / Platform / Software as a Service — differ
by how much the provider manages. *Here:* **Render = PaaS** (we give code, it runs it);
**MongoDB Atlas = DBaaS**; **Cloudinary = Storage/SaaS**. Examples: AWS EC2 (IaaS),
Heroku/Render (PaaS), Gmail (SaaS).

**6. HTTP vs REST.** HTTP is the transport **protocol** (requests/responses, methods GET/POST/
PUT/DELETE). REST is an **architectural style** for building APIs over HTTP around resources.
They are not the same: HTTP is the protocol, REST is a way to use it. *Here:* HTML pages use
GET/POST; our `/api/*` endpoints are a small REST/JSON API.

**7. API.** An interface that lets programs talk to each other through defined entry points,
hiding internal implementation. *Here:* we consume external APIs (Tavily, ClinicalTrials.gov,
Cloudinary) and expose our own JSON API under `/api/`.

**8. Docker.** Packages an app + its dependencies into a **container** so it runs the same
everywhere. Image = template, container = running instance, Dockerfile = build recipe. Lighter
than a full VM (shares the host kernel). *Here:* `Dockerfile` + `docker-compose.yml`; the
instructor's framing "a small local cloud".

**9. NoSQL.** "Not only SQL" — databases that aren't purely relational tables; flexible schemas
(documents, key-value, graph). Good for flexible/large data and horizontal scaling. *Here:*
MongoDB stores JSON-like documents.

**10. MongoDB.** A NoSQL **document** database. Hierarchy: **Database → Collections →
Documents** (JSON-like). *Here:* `medcloud` DB with `users`, `patients`, `prescriptions`, etc.

**11. Schema.** The structure of the data (which fields, which types). Relational schemas are
usually rigid and defined up front; NoSQL schemas can be flexible. *Here:* our models keep
consistent document shapes even though Mongo allows flexibility.

**12. Schema on write vs on read.** On **write** the structure is enforced when data is stored
(SQL). On **read** data is stored loosely and interpreted when read (Data Lakes/Big Data).

**13. MVC.** Model-View-Controller separates responsibilities. Model = data/logic, View = what
the user sees, Controller = handles requests and connects the two. *Here:* `models/` (Model),
`templates/` (View), `controllers/` (Controller), with a `services/` layer for logic/APIs.

**14. Scaling (linear vs non-linear).** Improving throughput by adding **hardware** (not
changing code). **Vertical** = a bigger server; **horizontal** = more servers. **Linear** =
performance grows ~proportionally to added resources; **non-linear** = it flattens due to a
bottleneck (DB, network). *Here:* add gunicorn workers/containers horizontally; Atlas scales
independently.

**15. Data Lake vs Database.** A **Database** stores structured operational data with a schema.
A **Data Lake** stores large amounts of raw/varied data (files, logs, images, JSON) for later
analysis. *Here:* our MongoDB is the operational database; raw uploaded images/PDFs are the
kind of raw content a data lake would hold.

**16. Data Center.** A physical facility full of servers, storage, network, power and cooling
where cloud services actually run. It's a full compute center, not just storage.

**17. Cloud service provider.** A company providing computing services over the internet.
Examples to name fast: **AWS, Azure, Google Cloud Platform** (also IBM Cloud).

**18. Network.** The full communication infrastructure — not just "connected computers" — but
protocols, addresses, routing and rules for moving data. It's what lets the app reach the DB
and external APIs.

**19. Model (abstraction).** An abstract representation of reality focused on what matters.
E.g. MVC is an architectural model; IaaS/PaaS/SaaS are cloud service models.

**20. Hadoop / Spark / Kafka (basic).** Big-data / distributed infrastructure. **Hadoop** =
distributed storage + processing (HDFS + MapReduce). **Spark** = a fast distributed compute
engine (in-memory). **Kafka** = a message/event routing platform for asynchronous
communication. *Here:* Kafka appears as a documented dispense-event stub.

---

## Static files vs Views/Templates (asked directly)
- **Templates/Views** (`app/templates/*.html`) are **rendered per request** by Jinja2 — the
  server injects data (patient list, prescription) into them.
- **Static files** (`app/static/css|js|images`) are **served as-is**, not rendered. They don't
  change per user/request. CSS and JS are static; the HTML pages are views.

## How to explain a random code file (the instructor's favorite)
For any file, answer four questions:
1. **Which MVC layer is it?** Model / View / Controller / Service / Static / Util.
2. **What requirement does it support?** (e.g. "doctor generates a prescription PDF").
3. **What cloud concept does it show?** (e.g. "consumes Cloudinary via its API").
4. **What happens if it fails?** (its fallback).

Example — `app/services/cloud_storage_service.py`: it's a **Service**; supports "save the
prescription PDF in the cloud"; demonstrates **cloud object storage via an API**; if Cloudinary
is unavailable it **falls back to local storage** so the feature still works.

## Folder-by-folder (layer · requirement · what to say)

| Folder | Layer | Requirement it supports | How to explain it orally |
|---|---|---|---|
| `app/controllers/` | **Controller** | All role flows (admin/doctor/pharmacist/auth/api) | "These are the Flask blueprints. They receive the HTTP request, validate the form, call a service or model, and return a template or a redirect. They're deliberately thin and never call external APIs." |
| `app/models/` | **Model** | Patients, visits, prescriptions, uploads, users, logs | "Each file is one data entity and its MongoDB persistence — how a document is built, saved and queried in its collection." |
| `app/services/` | **Service** | Cloud DB, PDF storage, OCR, search, clinical trials, AI validation | "This is the business logic and every external cloud API call. Isolating them here means the controller doesn't know about Cloudinary or Tavily, and each one has a fallback if the service is down." |
| `app/templates/` | **View** | All required pages | "Jinja2 templates — the Views. The server renders them per request and injects data like the patient list. `base.html` is the shared layout." |
| `app/static/` | **Static** | UI/UX requirement | "CSS, JavaScript and images. These are *not* views — they're served as-is and don't change per request." |
| `app/forms/` | **Form** | Input validation on every form | "WTForms classes. They give us server-side validation and CSRF protection for the login, patient, visit and upload forms." |
| `app/utils/` | **Utility** | Cross-cutting support | "Small helpers: `date_utils` calculates age from birth date, `decorators` enforces role-based access, `file_utils` saves uploads safely, `service_status` reports which cloud services are live vs fallback." |
| `scripts/` | **Script** | Provisioning a real database | "`seed_users.py` seeds the three demo accounts into a real MongoDB Atlas database. In demo mode the app seeds them automatically at startup." |
| `docs/` | **Docs** | PIV methodology + defense | "The PIV planning package: requirements, architecture, data model, cloud services, UI plan, roadmap, validation checklist, and this defense guide." |
| `tests/` | **Tests** | Validation phase of PIV | "Pytest suite driving the real flows through Flask's test client — auth/roles, patient CRUD, prescription+PDF, consultation fallbacks, and the pharmacist upload→OCR→dispense flow." |
| root | **Config/Entry** | Runtime + deployment | "`run.py` starts the app (gunicorn imports `run:app`); `Dockerfile`/`docker-compose.yml` containerise it; `render.yaml` deploys it; `requirements.txt` pins dependencies; `.env.example` documents every variable." |

## UI/UX (the instructor looks at this)
One consistent medical-dashboard theme, role-based navigation, tables, status badges, empty
states, and clear success/error messages — no raw/unstyled pages. The footer shows which
cloud services are live vs running in fallback, which is a good thing to point at during the demo.
