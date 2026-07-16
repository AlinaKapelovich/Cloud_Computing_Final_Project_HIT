# UI/UX Plan — MedCloud

The examiner explicitly grades look-and-feel, so the UI uses one consistent, professional
medical-dashboard design system (no default/unstyled pages).

## Design system
- **Single stylesheet** `app/static/css/styles.css` (no external CSS framework → easy to explain).
- **Palette:** clinical teal primary (`#0f766e`), calm neutrals, semantic colors for
  success/warning/danger/info.
- **Tokens:** CSS variables for colors, radius, shadow, sidebar width → consistent spacing.
- **Typography:** Segoe UI stack, large readable headings.

## Layout
- **App shell:** fixed left **sidebar** (role-based navigation) + **topbar** (page title, role
  badge, avatar, user name, logout) + scrollable content + **footer** with DB mode and a
  live/fallback **service status strip**.
- **Auth pages** use a centered card layout (no sidebar).
- **Responsive:** sidebar collapses behind a ☰ toggle under 860px; tables scroll horizontally
  inside `.table-wrap`; forms use responsive grids.

## Components (reused via Jinja macros)
- **Stat cards** (`stat_cards`) on every dashboard.
- **Status badges** (`status_badge`): open (blue), dispensed (green), cancelled (red).
- **Action cards** (`action_card`) for dashboard quick links. Every action card links to
  a real, working route — there is no "coming soon" placeholder state anywhere in the app.
- **Consultation panel** (`consult_panel`): input + results rendered from the JSON API.
- **Flash alerts**: success/danger/warning/info.
- **Empty states**: icon + message + call-to-action when a list is empty.
- **Forms**: WTForms rendered through `render_field` with inline error messages and focus states.

## Role dashboards
- **Admin:** patients / prescriptions stats (read-only oversight; Admin's scope is
  patient-record management — there is no staff/user-account management feature, so no
  such stat is shown) + patient list/search/create/edit actions.
- **Doctor:** patients / prescriptions / visits stats + start-visit / prescriptions / consult.
- **Pharmacist:** open / dispensed / uploads stats + find-patient / upload / side-effects,
  plus a "recent uploads" table so an upload not linked to a patient stays reachable.

## Required pages (all implemented & styled)
Login · role dashboards · patient list (with search)/create/edit/detail · select patient ·
new visit · new prescription (with diagnosis consultation) · prescription detail/list ·
pharmacist search (with side-effects consultation, reachable without a prior patient
search) · upload · OCR review (with AI-validation enforcement and manual-confirmation
checkbox) · 403/404/413/500/CSRF error pages.

## Feedback & states
- Every action gives a flash message (success/error).
- Missing-service situations show a clear info/warning message, never a raw error or JSON.
- The footer always shows whether each cloud service is **live** or in **fallback**.

## Accessibility / clarity
- High-contrast text, clear labels, large tap targets, semantic tables, descriptive buttons
  ("Dispense", "Create prescription & generate PDF") rather than vague labels.
