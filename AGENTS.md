# AGENTS.md — Project rules for AI agents working on MedCloud

This file guides any AI agent (or developer) contributing to MedCloud. It is **guidance**;
the **official source of truth** is the course requirements PDF in `הוראות/`. The concept
sheet and defense-questions notes are **preparation** material, not requirements. The
Node.js/Express demo in `הוראות/` is a **conceptual MVC reference only — never the stack**.

## Stack (do not change)
- **Flask / Python** application server.
- **Jinja2** templates = Views. **Flask blueprints/routes** = Controllers.
- **MongoDB Atlas** (cloud NoSQL) with in-memory `mongomock` fallback.
- **Cloudinary** for prescription PDF storage with local `generated_pdfs/` fallback.
- `services/` wrappers for every external API — controllers never call APIs directly.
- Deployment: **Docker + Render**. Bonus AI document validator implemented. **Kafka/Ollama =
  documented stubs only** unless all core flows are stable.

## PIV methodology
Work in three phases: **Planning** (docs in `docs/`) → **Implementation** (milestone by
milestone) → **Validation** (run smoke tests / route sweep; fix failures before continuing).
After each milestone: validate, check MVC separation, check fallbacks, check UI, then proceed.

## MVC rules
- Controllers stay **thin**: validate input, call a service/model, return a template/redirect.
- Business logic and all external API calls live in `app/services/`.
- Models (`app/models/`) hold data entities + MongoDB persistence only.
- Templates are Views; `static/` holds CSS/JS/images (not views).

## Language rules
- All code, comments, docs and commit notes in **English**. No Hebrew in code/comments.
- User-facing UI text is English.

## Cloud-service fallback rules
Every external call must handle: missing key, timeout, invalid response, empty result,
service unavailable — and degrade to a **documented fallback** with a clear UI message. The
app must start and demo end-to-end with **zero external credentials**. Never hardcode secrets;
read them from env vars; keep `.env` git-ignored and `.env.example` updated.

## UI/UX rules
Keep the single medical-dashboard design system (`app/static/css/styles.css`). No raw/unstyled
pages. Use cards, tables, status badges, empty states, and clear success/error messages.

## Defense-readiness rules
For every major file it must be easy to say: which MVC layer, which requirement it supports,
which cloud concept it demonstrates, and what happens if it fails. Keep `docs/DEFENSE_GUIDE.md`
current with the concept answers and the "explain a random file" playbook.

## Priority
Core Admin/Doctor/Pharmacist flows first and stable, then bonuses. Do not break core
functionality for a bonus. Prefer simple, explainable code over cleverness.

## Safety
Do not delete or overwrite the course materials in `הוראות/` and `תמלולי הרצאות/` — they are
references only.
