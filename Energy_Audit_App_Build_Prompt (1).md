# Build Prompt: Energy Audit App (Multi-Institution, PostgreSQL)

You are a senior full-stack developer. Build the web application described below, end to end, in clean, readable, well-structured code. Follow the exact project structure in Section 4 and work in the stages listed in Section 12. Finish one stage completely (code runs, tests pass), give me a short summary, then continue to the next stage.

---

## 1. Goal

A web app that lets auditors at **different institutions** (colleges, schools, hospitals, offices) assess electricity use in a small number of buildings, find inefficient equipment and practices, and produce a basic audit report per building.

Core path: **register institution -> buildings -> monthly energy data -> analysis (EUI, charts, anomalies) -> equipment inventory and reconciliation -> audit checklist findings -> recommendations with simple payback -> PDF report.**

It is a decision-support prototype. Data is entered manually or imported from CSV.

## 2. Hard constraints

- **Database: PostgreSQL.** Multi-tenant: many institutions share one database; each sees only its own data.
- **No devops.** No Docker, CI/CD, hosting, cloud config or deployment scripts. The app runs locally with `npm install` and a local PostgreSQL. Provide a `.env.example` and a README with local setup steps only.
- **Out of scope, do not build:** utility/smart-meter integrations, NPV/IRR/life-cycle costing, carbon accounting, weather normalisation, verified savings, AI predictions, campus hierarchies or departments, approval chains, email notifications, offline sync, solar assessment, client portal.
- Label every savings figure as an **estimate**, never a verified result.
- Do not invent features beyond this prompt. If something is ambiguous, pick the simplest reasonable option and note it in the README.

## 3. Tech stack

- **Front end:** React (Vite), React Router, Chart.js via react-chartjs-2, plain CSS with CSS variables (no UI framework). JavaScript (ES modules).
- **Back end:** Node.js, Express, `pg` (node-postgres), Zod for validation, bcrypt, jsonwebtoken (JWT in an httpOnly cookie), multer (photo upload), Puppeteer for PDF (plus a print-friendly report page as fallback).
- **Migrations:** plain SQL files run in order with `node-pg-migrate` (or a tiny custom runner).
- **Tests:** Vitest or Jest, plus Supertest for the API, using a separate test database.

## 4. Project structure (create exactly this layout)

One repository with two independent apps, **`client/`** (React) and **`server/`** (Express API), each with its own `package.json`. A root `package.json` only holds convenience scripts (`dev` runs both with `concurrently`, `test`, `migrate`, `seed`).

```
energy-audit/
  package.json            root scripts only: dev, test, migrate, seed
  README.md               local setup steps (no deployment)
  client/                 FRONTEND  (React + Vite)
  server/                 BACKEND   (Node + Express + PostgreSQL)
```

### 4.1 Frontend structure: `client/`

```
client/
  index.html
  package.json
  vite.config.js            dev proxy: /api -> http://localhost:4000
  src/
    main.jsx                React entry, router, providers
    App.jsx                 route table and layout wiring

    routes/
      ProtectedRoute.jsx    redirects to /login if not signed in
      RoleRoute.jsx         admin-only pages (Users, Settings)

    context/
      AuthContext.jsx       user, institution name, role, login(), logout()

    api/                    ONLY place that calls fetch
      client.js             fetch wrapper: credentials 'include', JSON, error mapping
      auth.js  institution.js  users.js  buildings.js  energy.js
      equipment.js  findings.js  recommendations.js  measures.js  reports.js

    pages/                  one file per screen; compose components, hold page state
      Register.jsx  Login.jsx  ChangePassword.jsx
      Dashboard.jsx  Buildings.jsx  EnergyRecords.jsx  Equipment.jsx
      Audit.jsx  Recommendations.jsx  Reports.jsx
      Users.jsx  Settings.jsx  NotFound.jsx

    components/
      layout/               AppLayout.jsx  TopBar.jsx  SideNav.jsx (role-aware)
      ui/                   Button.jsx  FormField.jsx  DataTable.jsx  StatusChip.jsx
                            Alert.jsx  ConfirmDialog.jsx  Spinner.jsx  EmptyState.jsx
      charts/               MonthlyConsumptionChart.jsx  EuiComparisonChart.jsx
                            EndUseChart.jsx  TrendChart.jsx   (Chart.js wrappers)
      domain/               BuildingSelector.jsx  CsvImportPanel.jsx
                            ReconciliationPanel.jsx  AnomalyBanner.jsx
                            FindingForm.jsx  RecommendationCard.jsx  ReportPreview.jsx

    hooks/                  useApi.js (loading/error/data)  useBuildings.js  useAuth.js

    utils/                  csvParser.js  formatters.js (numbers, currency, dates)
                            validators.js (client-side checks, mirror the server)

    styles/                 tokens.css (colour/spacing variables)  base.css
                            layout.css  components.css
```

**Frontend rules**
- Pages compose components; components never call `fetch` directly. All HTTP goes through `api/` (usually via `hooks/`).
- Every data screen has loading, error and empty states.
- Client-side validation gives fast feedback, but the server is the authority.
- Colours and spacing come only from `styles/tokens.css`.
- The menu hides Users and Settings for auditors, and `RoleRoute` also blocks them.
- The institution name is always visible in `TopBar`.

### 4.2 Backend structure: `server/`

```
server/
  package.json
  .env.example              DATABASE_URL, JWT_SECRET, PORT, UPLOAD_DIR, COOKIE settings
  src/
    server.js               starts the HTTP server
    app.js                  Express setup: middleware, routes, error handler

    config/
      env.js                loads and validates environment variables

    db/
      pool.js               pg Pool (non-superuser app role)
      withTenant.js         BEGIN -> set_config('app.institution_id') -> fn(client) -> COMMIT
      migrations/           001_institutions_users.sql   002_buildings.sql
                            003_energy_records.sql       004_equipment.sql
                            005_findings.sql             006_recommendations_measures.sql
                            007_rls_policies.sql         008_auth_functions.sql
      seed/                 seed.js  measures.js  demoData.js

    middleware/             requireAuth.js  requireRole.js  tenantContext.js
                            validate.js  upload.js  rateLimit.js
                            errorHandler.js  notFound.js

    routes/                 HTTP only: parse request, call a service, send response
      index.js              mounts all routers under /api
      auth.routes.js  institution.routes.js  users.routes.js  buildings.routes.js
      energy.routes.js  equipment.routes.js  findings.routes.js
      recommendations.routes.js  measures.routes.js  reports.routes.js  export.routes.js

    validators/             Zod schemas
      auth.schema.js  user.schema.js  building.schema.js  energy.schema.js
      equipment.schema.js  finding.schema.js  recommendation.schema.js

    services/               business logic; calculation services are PURE functions (no DB)
      auth.service.js  buildings.service.js  energy.service.js (incl. CSV import)
      analysis.service.js  anomaly.service.js  reconciliation.service.js
      payback.service.js  equipment.service.js  findings.service.js
      recommendations.service.js  report.service.js  export.service.js

    repositories/           ONLY place with SQL; always use the tenant-scoped client
      institutions.repo.js  users.repo.js  buildings.repo.js  energy.repo.js
      equipment.repo.js  findings.repo.js  recommendations.repo.js  measures.repo.js

    utils/                  errors.js (AppError, NotFoundError, ValidationError, ForbiddenError)
                            asyncHandler.js  csv.js  dates.js

    templates/              report.html  report.css   (rendered to PDF by Puppeteer)

  uploads/<institution_id>/ finding photos and generated reports

  tests/
    unit/                   analysis  anomaly  reconciliation  payback
    api/                    auth  buildings  energy  roles
    isolation/              tenant-isolation.test.js  rls.test.js
    helpers/                testDb.js  factories.js
```

**Backend rules**
- **Request flow:** `route -> requireAuth -> requireRole (if needed) -> tenantContext -> validate (Zod) -> handler -> service -> repository`.
- `tenantContext` opens a transaction, sets `app.institution_id` from the JWT, and exposes the tenant-scoped client as `req.db`; it commits on success and rolls back on error.
- Layers only call downwards: routes call services, services call repositories, repositories run SQL. No SQL outside `repositories/` and `db/`.
- Calculation services (`analysis`, `anomaly`, `reconciliation`, `payback`) take plain data and return plain data, so they can be unit tested without a database.
- Errors are thrown as `AppError` subclasses and converted to `{ error, details }` JSON by `errorHandler`. A record from another institution returns 404.
- Never read the institution id from the URL or request body; only from the token.

### 4.3 How the two apps connect
- The React app calls only relative `/api/...` URLs. In development, Vite proxies them to the Express server on port 4000.
- Authentication is an httpOnly cookie, so the client sends `credentials: 'include'` and never handles the token.
- The JSON endpoints in Section 8 are the contract between the two; keep field names identical on both sides (snake_case in the database, camelCase in JSON via a small mapping in the repositories).

## 5. Database design (PostgreSQL)

Use `bigint GENERATED ALWAYS AS IDENTITY` keys, `numeric` for kWh and money, `date` for months (always the first day), `timestamptz` for timestamps, and CHECK constraints so the database rejects bad data even if the API is wrong.

**Tables (every table except `institutions` has `institution_id bigint NOT NULL`):**

- `institutions`: id, name (unique), currency (char(3), default 'KES'), max_buildings (int, default 5, 1 to 50), created_at.
- `users`: id, institution_id, name, email (unique across the system), password_hash, role ('admin' or 'auditor'), must_change_password (bool), created_at.
- `buildings`: id, institution_id, name, type, floor_area_m2 (> 0), operating_hours (1 to 24). UNIQUE (institution_id, name) and UNIQUE (institution_id, id).
- `energy_records`: id, institution_id, building_id, month (date, day = 1), kwh (>= 0), cost (>= 0). UNIQUE (building_id, month).
- `equipment`: id, institution_id, building_id, category ('lighting', 'ac_ventilation', 'motors_pumps', 'ict', 'other'), name, location, rating_w (> 0), qty (> 0), hours_day (0 to 24), days_year (0 to 366), condition (optional).
- `findings`: id, institution_id, building_id, area ('lighting', 'ac_ventilation', 'motors_pumps', 'operating_hours', 'practices'), problem, location_system, suggested_improvement, priority ('Low', 'Medium', 'High'), photo_path (nullable), created_at.
- `recommendations`: id, institution_id, building_id, finding_id (nullable), measure_id (nullable), title, estimated_cost (>= 0), estimated_annual_saving (>= 0), status ('Proposed', 'Accepted', 'Implemented'), is_estimate (always true), created_at.
- `measures_library`: id, institution_id (NULL = system preset), name, category, typical_saving_pct, typical_cost, description.

**Integrity:** child tables use composite foreign keys `(institution_id, building_id) REFERENCES buildings (institution_id, id) ON DELETE CASCADE` so a row can never point at another institution's building.

**Row-level security (required):**
- `ENABLE` and `FORCE ROW LEVEL SECURITY` on every tenant table.
- Policy: `USING` and `WITH CHECK` `institution_id = current_setting('app.institution_id', true)::bigint`.
- `measures_library`: read policy also allows `institution_id IS NULL`; write policy allows only the caller's institution.
- The app connects with a **non-superuser role without BYPASSRLS**. Migrations run as the owner.
- Implement `withTenant(institutionId, fn)`: take a pooled client, `BEGIN`, `SELECT set_config('app.institution_id', $1, true)`, run `fn(client)`, `COMMIT` (or `ROLLBACK` on error), release.
- Login and institution sign-up happen before a tenant is known. Handle them with `SECURITY DEFINER` SQL functions (for example `auth_lookup(email)` and `register_institution(...)`) rather than weakening the policies.

**Seed data** (separate seed script):
- 8 system measures (LED retrofit, occupancy sensors, efficient AC, AC schedule/switch-off, VFD on pumps, power factor correction, timer on water heating, staff awareness) with typical saving % and cost.
- Two demo institutions, each with an admin and an auditor, 2 buildings of the same type, 12 months of electricity data per building (one deliberately high month), 5 to 8 equipment items, 4 to 6 findings, 2 recommendations. Use fictional names.

## 6. Auth, roles and tenancy

- Institution sign-up creates the institution and its first admin in one transaction. Passwords at least 8 characters, hashed with bcrypt.
- Login returns a JWT (user id, institution id, role) in an httpOnly, sameSite cookie. Rate-limit login attempts.
- The **institution id always comes from the token**, never from the URL or body.
- Admin creates auditor accounts with a temporary password (`must_change_password = true`); the user must change it at first login. No email.
- **Admin:** manage users and institution settings (name, currency, building limit), delete data. **Auditor:** create and edit buildings, records, equipment, findings, recommendations and reports; cannot manage users or settings.
- Another institution's record must return **404**, as if it did not exist.

## 7. Business logic (server `services/`, pure functions, fully unit tested)

```
Annual kWh / cost         = sum of the 12 monthly values
EUI (kWh/m2/year)         = annual kWh / floor_area_m2
Equipment annual kWh      = rating_w * qty * hours_day * days_year / 1000
End-use share (%)         = category kWh / total inventory kWh * 100
Reconciliation gap (%)    = (billed kWh - inventory kWh) / billed kWh * 100
Simple payback (years)    = estimated_cost / annual cost saving
```

- **EUI** only when 12 months exist; otherwise show consumption so far and label EUI "incomplete".
- **Anomaly flag:** a month more than 30% above the average of that building's other months (constant is configurable).
- **Comparison:** compare buildings by EUI within the same institution; if building types differ, show a warning that the comparison may not be fair.
- **Reconciliation:** warn when the absolute gap exceeds 15% (inventory usually covers only audited equipment).
- **Payback:** cost 0 shows "Immediate"; saving 0 shows "Not applicable"; never divide by zero.
- A recommendation can be created from a library measure: pre-fill title, cost, and a saving estimate (typical saving % of the relevant baseline cost); the auditor can edit everything.

## 8. API (JSON under `/api`, all routes need a session except sign-up and login)

- `POST /auth/register-institution`, `POST /auth/login`, `POST /auth/logout`, `POST /auth/change-password`
- `GET, PATCH /institution`; `GET, POST, PATCH, DELETE /users` (admin only)
- `GET, POST /buildings` (enforce the institution's `max_buildings`); `GET, PATCH, DELETE /buildings/:id`
- `GET, POST /buildings/:id/energy`; `POST /buildings/:id/energy/import` (CSV: validate, return per-row errors, import only after confirmation); `PATCH, DELETE /buildings/:id/energy/:recId`
- `GET /buildings/:id/analysis` (annual totals, EUI, monthly series, anomalies); `GET /analysis/compare`
- `GET, POST, PATCH, DELETE /buildings/:id/equipment`; `GET /buildings/:id/reconciliation`
- `GET, POST, PATCH, DELETE /buildings/:id/findings` (photo upload: JPG or PNG, max 5 MB, random file name, stored in the institution's folder, served only through an authenticated route)
- `GET, POST, PATCH, DELETE /buildings/:id/recommendations`
- `GET, POST /measures` (system presets plus the institution's own)
- `GET /buildings/:id/report` (report data; PDF download)
- `GET /export` (the institution's data as JSON or CSV)

Validate every request with Zod. Use parameterised queries only. Return consistent error JSON: `{ error, details }`.

## 9. Validation rules

- Monthly record: month `YYYY-MM` (stored as first of month), kWh and cost required, numeric, not negative, month not already recorded for that building.
- CSV import: columns `month,kwh,cost`; validate each row; list invalid rows with row numbers; do not import anything until the user confirms the valid rows.
- Building: name required and unique within the institution; floor area positive; operating hours 1 to 24; limit not exceeded.
- Equipment: rating and quantity positive; hours_day 0 to 24; days_year 0 to 366.
- Recommendation: cost and saving not negative; status one of the three values.

## 10. Screens and UI

Layout: top bar (app name, institution name, user, logout) and a left navigation that follows the workflow: Dashboard, Buildings, Energy Records, Equipment, Audit, Recommendations, Reports, plus Users and Settings for admins only. Plus Register and Login pages.

- **Dashboard:** building count, total kWh, total cost, monthly consumption chart for all buildings, EUI comparison bars with a caveat, anomaly alerts.
- **Buildings:** table with add, edit, view; "Add building" disabled at the institution's limit.
- **Energy Records:** building selector, add form, CSV import with error list, trend chart, record table with anomaly flags.
- **Equipment:** inventory table with calculated annual kWh and share, end-use pie chart, reconciliation panel with warning.
- **Audit:** tabs for the five checklist areas; each lists findings and has an add form (problem, location/system, suggested improvement, priority, optional photo).
- **Recommendations:** cards with cost, estimated annual saving, payback, status chip, "Estimate" label; "Add from measures library".
- **Reports:** per-building preview with sections: building profile, consumption and cost summary, EUI and chart, audit findings, recommendations with payback, short conclusion (editable text). Export PDF or print.
- **Users / Settings (admin):** user list with roles and temporary-password status; institution name, currency, building limit.

Visual style: deep green `#1F7A4D` for navigation and primary buttons, light green `#E8F3EC` panels, amber `#F2A900` warnings, red only for errors, blue `#3B7DD8` secondary data series. Priority chips: Low grey, Medium amber, High red. Status chips: Proposed amber, Accepted blue, Implemented green. Inline field errors, banner alerts, confirmation before deleting. Labelled inputs, keyboard-friendly, good contrast, charts with a data table beneath. Designed for laptop screens.

## 11. Testing (must pass before finishing)

- **Unit tests:** EUI, annual totals, equipment kWh, reconciliation gap, anomaly flag, payback (including zero cases), using hand-calculated examples.
- **API tests:** validation errors (negative kWh, duplicate month, exceeding the building limit, bad CSV rows), role restrictions, blocked access without login.
- **Isolation tests:** create two institutions; prove a user of one cannot list, read, edit or delete the other's data via the API, and that a direct SQL query without `app.institution_id` returns zero rows.

## 12. Build order (stop after each stage with a short summary)

1. PostgreSQL migrations, RLS policies, `withTenant()`, SECURITY DEFINER auth functions, institution sign-up, login, tenant middleware. Isolation tests.
2. Building records, user management, institution settings.
3. Monthly energy entry, CSV import, validation.
4. Analysis service (totals, EUI, anomalies), charts, Dashboard, comparison.
5. Equipment inventory, end-use chart, reconciliation.
6. Audit checklist and findings with photo upload.
7. Recommendations, measures library, payback.
8. Report page, PDF export, seed script, README, final test run.

## 13. Definition of done

Running the seed and starting the app, I can: sign up a new institution; add two buildings; enter or import 12 months for each; see charts, EUI and the comparison with its caveat; see the anomaly flag; add equipment and see reconciliation; record findings (one with a photo); add a recommendation from the library and one by hand with payback; export a building report as PDF; and confirm a second institution sees none of the first institution's data. All tests pass, and the README explains local setup in a few commands.

## 14. How to respond

At the start, confirm the frontend and backend folder structures from Section 4 (create the empty folders and placeholder files) and list any assumptions. After each stage, give: what was built, how to run it, and test results. Keep code commented where the logic is non-obvious (especially RLS, `withTenant` and the calculations).
