# What has been built

Related docs: [Simplified architecture](simplified-architecture.md) · [Architecture](architecture.md) · [API reference](api.md) · [Formulas](formulas.md)

## Phase 1 — Foundation & auth (complete)
- Flask app factory (`create_app`) with config classes (dev/testing)
- MySQL + Flask-SQLAlchemy with tenant-scoped models
- Auth: institution registration (creates institution + admin in one txn), login, logout, change-password
- JWT Bearer tokens, bcrypt passwords (min 8 chars), `must_change_password` for admins
- Error hierarchy (`ApiError` → `ValidationError`/`BusinessError`/`NotFoundError`/`UnauthorizedError`/`ForbiddenError`)
- Response envelopes (success/error), named logging, validators
- 19 tests passing (phase 1)

## Phase 2 — Institutions, users, buildings (complete)
- Institution settings: name, currency, standard electricity rate per kWh, max_buildings (admin-only patch)
- Users: CRUD (admin only), auditor creation with temp password, self-delete blocked
- Buildings: CRUD (both roles), name unique per institution, floor area > 0, operating hours 1–24, max_buildings enforcement
- `require_role` decorator, shared password utils, single blueprint registration loop
- Cross-tenant access → 404

## Phase 3 — Energy records & CSV import (complete)
- `EnergyRecord` model: month as first-of-month Date, kwh/cost non-negative, unique per building+month, composite tenant FK with cascade
- CRUD at `/api/buildings/:id/energy` (duplicate month → 409, invalid input → 400, cross-tenant → 404)
- CSV import: validate-first, per-row errors, confirm-before-import; pure `parse_energy_csv` util

## Phase 4 — Analysis engine & dashboard (complete)
- `analysis.py`: pure functions — annual kWh/cost, EUI, monthly series, anomaly detection (>30% above average of other months), building comparison with fairness warning, month aggregation
- `dashboard_service.py`: building analysis, comparison, dashboard summary (totals aggregated across all buildings)
- Endpoints: `GET /buildings/:id/analysis`, `GET /analysis/compare`, `GET /dashboard`
- Pure unit tests for EUI, anomaly threshold, comparison warning, aggregation

## Frontend (Phases 1–4)
- Server-rendered Jinja2 templates, vanilla JS, plain CSS (no SPA)
- Professional navy/teal/amber brand, light mode default, dark mode toggle (persisted)
- Layout: topbar (64px) + sidebar (240px desktop) + content area
- Pages: Login, Register, Dashboard, Buildings, Energy Records, Users, Settings, Compare
- Dashboard: populated stat cards (total kWh, total cost, building count, anomaly count), monthly consumption bar chart, anomaly list, and building performance table.
- Buildings: add/edit/delete, view energy link
- Users: add (admin only), list, delete
- Settings: institution name/currency/standard electricity rate/max_buildings patch
- Energy records: building selector, add form with automatic KSh cost calculation from the standard rate, CSV import with per-row errors + confirmation, record list/delete, monthly analysis chart and anomaly list
- Compare: EUI table with data-coverage badges, fairness warning, and EUI bar chart
- Client-side session gate: token stored in localStorage, `/api/auth/session` verification, unauthenticated `/dashboard` → `/login`

## Tests
- **81 tests passing** (auth, error envelopes, roles, tenant isolation, limits, energy import, analysis formulas, page rendering)

## Infrastructure
- `create_database.py`: standalone DB bootstrap (reads `MYSQL_*` env via `build_database_url()`)
- Alembic configured (`migrations/env.py` uses app's `build_database_url()`; `migrations/versions/` gitignored)
- File-based logging (`logs/energy_audit.log` + console), level from `LOG_LEVEL` env (default DEBUG)
- `.env.example`, `.gitignore`, `requirements.txt`, `run.py`, `PHASE_TRACK.md`, `README.md`

## Remaining phases (not built)
- Phase 5 — Equipment & reconciliation (equipment CRUD, reconciliation gap %, simple payback)
- Phase 6 — Findings & recommendations (audit checklist, library measures, payback)
- Phase 7 — Reports, PDF (WeasyPrint), export, seed script, final validation

## Future enhancement — Centralized platform super-admin (not built)
The current model is multi-tenant with institution-scoped admins. There is no platform-level super-admin who can create, suspend, or manage institutions across tenants. A future step could add:
- A separate platform super-admin role and authentication path
- Institution lifecycle management (create, suspend, archive, set limits and standard rate)
- Cross-tenant read-only reporting and support access with an audit trail
- Platform-wide usage metrics and billing hooks

This is deliberately out of scope for Phases 1–4 and should be designed as a separate phase.
