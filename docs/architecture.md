# Architecture — Energy Audit App

## Overview
Server-rendered multi-institution Energy Audit App using Python/Flask, MySQL, Jinja2 templates, vanilla JS (no SPA), plain CSS, and Chart.js. Tenant isolation is handled at the application layer (no PostgreSQL RLS).

## Stack
| Layer | Tech |
|-------|------|
| Language | Python 3.13 |
| Web framework | Flask |
| ORM | Flask-SQLAlchemy |
| Database | MySQL (via `mysql-connector-python`) |
| Auth | PyJWT (Bearer), bcrypt |
| Frontend | Jinja2 server-rendered templates, vanilla JS (ES modules), plain CSS, Chart.js (CDN) |
| PDF | WeasyPrint |
| Testing | pytest |
| Migrations | Alembic |
| Env config | python-dotenv |

## Directory layout
```
server/
  __init__.py          # Flask app factory (create_app)
  config.py            # Env config, build_database_url(), Logging config
  extensions.py        # SQLAlchemy db instance
  errors.py            # ApiError hierarchy + error handlers
  responses.py         # success_response / error_response envelopes
  logging.py           # File + console logging (LOG_LEVEL env, default DEBUG)
  decorators.py        # require_auth, require_role
  models/
    __init__.py        # db + model exports
    institution.py     # Institution model
    user.py            # User model (admin / auditor)
    building.py        # Building model
    energy_record.py   # Energy record model
  repositories/
    __init__.py
    building_repo.py
    institution_repo.py
    user_repo.py
    energy_repo.py
  services/
    __init__.py
    auth_service.py    # Register, login, logout, change-password, session, JWT
    institution_service.py
    users_service.py
    buildings_service.py
    energy_service.py
    dashboard_service.py
    analysis.py        # Pure calculation functions (totals, EUI, anomaly, compare)
  schemas/
    auth_schema.py
    building_schema.py
    energy_schema.py
    institution_schema.py
    user_schema.py
  utils/
    validators.py
    security.py        # bcrypt hash/verify
    dates.py           # month parsing
    csv.py             # CSV parsing
  blueprints/
    __init__.py        # blueprints list
    auth_bp.py         # /api/auth routes
    institution_bp.py  # /api/institution
    users_bp.py        # /api/users
    buildings_bp.py    # /api/buildings
    energy_bp.py       # /api/buildings/:id/energy (+ import)
    analysis_bp.py     # /api/analysis (+ compare, dashboard)
    pages_bp.py        # server-rendered HTML routes
tests/
  api/
  unit/
migrations/            # Alembic
server/templates/      # Jinja2 HTML templates
server/static/css/     # Styles (light/dark via CSS variables)
server/static/js/      # Vanilla JS (auth, charts)
create_database.py     # Standalone bootstrap (creates MySQL DB)
```

## Design principles
- **One blueprint per domain**, registered via a single `blueprints` list in `blueprints/__init__.py`.
- **One module = one concern.**
- **Two error branches:** boundary/request errors (`ValidationError`) vs business-rule errors (`BusinessError`), rooted in `ApiError`.
- **Response envelopes:** success `{status, message, data[, meta]}`, error `{status, message, errors}`.
- **JSON-object bodies only.** No defaulting on non-object bodies.
- **Identity from `Authorization: Bearer` header only.** No cookies.
- **Tenant isolation:** every child table has `institution_id` + composite FK `(institution_id, building_id)` → `buildings(institution_id, id)`. Institution ID comes from the JWT, never from URL/body.
- **Commit once per request**, session removed on teardown.
- **Named loggers**, file + console output, level from `LOG_LEVEL` env (default DEBUG).

## Database relationships
```
institutions (id PK, name, currency, max_buildings, created_at)
    └── users (id PK, institution_id FK, name, email, role, password_hash, must_change_password)
    └── buildings (id PK, institution_id FK, name, type, floor_area_m2, operating_hours)
        └── energy_records (id PK, institution_id, building_id FK composite, month, kwh, cost)
```

## Environment variables
| Var | Default | Purpose |
|-----|---------|---------|
| `DATABASE_URL` | built from `MYSQL_*` | Full SQLAlchemy DB URI (alternative to `MYSQL_*`) |
| `MYSQL_HOST` | `127.0.0.1` | MySQL host |
| `MYSQL_PORT` | `3306` | MySQL port (empty = omit port) |
| `MYSQL_USER` | `root` | MySQL user |
| `MYSQL_PASSWORD` | `root` | MySQL password |
| `MYSQL_DATABASE` | `energy_audit` | Database name |
| `JWT_SECRET` | dev default | JWT signing secret |
| `LOG_LEVEL` | `DEBUG` | Logging level |
| `CORS_ORIGINS` | (empty) | Allowed origins (empty = none) |

## Bootstrap script
`create_database.py` — reads `DATABASE_URL` (or `MYSQL_*` vars), connects to MySQL, and runs `CREATE DATABASE IF NOT EXISTS`. Run once before `create_all()`.
