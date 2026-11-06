# Architecture — Information Flow

This document describes how a request travels through the app, from HTTP wire to database and back. It is **not** a file listing.

## Core request lifecycle (every request)

```
Browser / curl
     │
     ▼
create_app()  (server/__init__.py)
     │
     ├─ extensions.db.init_app(app)          # bind SQLAlchemy
     ├─ errors.register_error_handlers(app)  # ApiError → JSON envelopes
     ├─ logging.register_error_logger(app)   # file + console, LOG_LEVEL env
     ├─ register all blueprints              # one blueprint per domain
     └─ before_request: enforce_origin()     # CORS origin backstop
     │
     ▼
Route matched → Blueprint handler
     │
     ├─ require_auth decorator               # Bearer token → g.current_user
     │     ├─ read Authorization header
     │     ├─ decode JWT (sub=user id, institution_id, role)
     │     ├─ UserRepository().find_by_id(sub)
     │     └─ store user on Flask g (request-local)
     │
     └─ Schema validation (if body)          # required fields, types, ranges
           │
           ▼
Service layer (business rules)
     │
     ├─ Repository queries                     # tenant-scoped SQL
     │     └─ WHERE institution_id = g.current_user.institution_id
     │           AND ... (building_id, etc.)
     │
     └─ Return plain dict / model
           │
           ▼
Blueprint returns success_response(...) or raises ApiError
     │
     ├─ success → {status:"success", message, data}
     ├─ ApiError  → {status, message, errors} with exc.status_code
     └─ unexpected → 500 {status:500, message:"internal server error"}
     │
     ▼
Flask returns JSON to client
     │
     ▼
extensions.db.session.remove()  (teardown_appcontext)
```

## Auth flow (login → authenticated requests)

```
1. POST /auth/register-institution
   Body: {institution_name, admin_name, admin_email, password}
   Service: Institution + User(admin) created in ONE transaction.
            Password hashed with bcrypt, must_change_password=True.
   Returns: access_token (JWT), institution_id, user_id.

2. POST /auth/login
   Body: {email, password}
   Service: find user by email, verify bcrypt, issue JWT:
            sub=user.id, institution_id, role, iat, exp.
   Returns: access_token.

3. Every subsequent request:
   Client sends: Authorization: Bearer <access_token>
   require_auth:
     - decode JWT → payload.sub, payload.institution_id, payload.role
     - UserRepository().find_by_id(sub) → g.current_user
     - All repository queries for this request are scoped to
       g.current_user.institution_id.
   If token missing/invalid → 401 UnauthorizedError.
```

## Tenant isolation flow (the "one institution" rule)

Every child table has `institution_id` and a **composite foreign key**:

```
buildings.institution_id references institutions.id
energy_records.(institution_id, building_id) references buildings.(institution_id, id)
```

Flow for any data request (e.g., `GET /buildings/5/energy`):

```
1. require_auth → g.current_user (institution_id = 42)
2. buildings_service.list_records(user, building_id=5)
   → EnergyRepository().list_for_building(
       institution_id=42, building_id=5
     )
   → SQL: WHERE institution_id = 42 AND building_id = 5
3. If no row matches → NotFoundError → 404 (cross-tenant looks like "not exist")
```

Result: Institution A can never see Institution B's buildings/records/users because every query is filtered by `institution_id` from the JWT, and the URL/body never supplies the institution.

## Energy record flow

```
POST /buildings/:id/energy
Body: {month, kwh, cost}
│
├─ require_auth (user from JWT)
├─ energy_schema: month YYYY-MM, kwh >= 0, cost >= 0
├─ service: building belongs to user's institution?
├─ service: month not already recorded for this building?
│   → duplicate → 409 BusinessError
├─ repo: INSERT energy_records (institution_id, building_id, month, kwh, cost)
│   → commit once
└─ return created record
```

## CSV import flow (validate-then-confirm)

```
POST /buildings/:id/energy/import
Body: {csv: "month,kwh,cost\n...", confirm: false|true}

1. validate_import_payload: csv is string, confirm is boolean
2. parse_energy_csv(text) — pure function, no DB:
   - header must be exactly month,kwh,cost
   - each row: month YYYY-MM, kwh >= 0 number, cost >= 0 number
   - duplicate months within file flagged
   - returns (parsed_rows, errors with row numbers)
3. If confirm == false:
     return {valid_rows, errors, imported: 0, requires_confirmation: true}
     (NOTHING is written to DB)
4. If confirm == true:
     for each parsed row:
       - month already recorded for this building? → error, skip
       - else repo.create(...)
     commit once
     return {valid_rows, errors, imported: N}
```

## Analysis / dashboard flow

```
GET /buildings/:id/analysis
│
├─ require_auth
├─ dashboard_service.analyze_building(user, building_id)
│   ├─ repo: building belongs to institution?
│   ├─ repo: all energy records for this building
│   ├─ analysis.annual_kwh(records)   = sum kwh
│   ├─ analysis.annual_cost(records)  = sum cost
│   ├─ analysis.eui(total_kwh, floor_area)   = None if <12 months
│   ├─ analysis.anomaly_months(records)      = month >30% above avg of others
│   └─ return dict
└─ return JSON with totals, EUI, note (complete/partial/insufficient), anomalies

GET /analysis/compare
│
├─ for each building in institution:
│   ├─ annual kWh/cost, EUI
│   └─ collect building types
├─ analysis.compare_buildings(analyses, types)
│   └─ warning if >1 distinct building type
└─ return {comparisons, warning}

GET /dashboard
│
├─ for each building: total kWh, total cost (ALL buildings, even incomplete)
├─ monthly_series aggregated across buildings by month
├─ comparisons (only buildings with complete EUI)
├─ anomalies collected across all buildings
└─ return {building_count, total_kwh, total_cost, monthly_series, comparisons, warning, anomalies}
```

## Response envelopes

Success (from `responses.success_response`):
```json
{ "status": "success", "message": "...", "data": { ... }, "meta": null }
```

Error (from `server/errors.py` handlers):
```json
{ "status": 400, "message": "...", "errors": { "field": ["reason"] } }
```

Unexpected exception → 500 `{ "status": 500, "message": "internal server error", "errors": {} }`, logged via `app.logger.exception`.

## Configuration flow

```
Environment variables (or .env)
     │
     ├─ MYSQL_HOST/PORT/USER/PASSWORD/DATABASE
     │     └─ build_database_url() → SQLALCHEMY_DATABASE_URI
     │           (port omitted if MYSQL_PORT empty → PythonAnywhere safe)
     ├─ JWT_SECRET, JWT_EXPIRATION_SECONDS, BCRYPT_ROUNDS
     ├─ CORS_ORIGINS (empty = none allowed)
     ├─ LOG_LEVEL (default DEBUG) → logging.py
     └─ DATABASE_URL (override for full URL, bypasses MYSQL_*)
           │
           ▼
create_app(config_object) loads the class, builds the URL,
initializes extensions, registers blueprints and handlers.
```

## What is NOT built yet (phases 5–7)
- Equipment CRUD, reconciliation gap %, simple payback
- Findings & recommendations (library measures, payback)
- Reports, PDF (WeasyPrint), export, seed script, final validation
