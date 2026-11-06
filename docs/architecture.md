# Architecture — Information Flow

Related docs: [API reference](api.md) · [Formulas](formulas.md) · [What has been built](what-has-been-built.md)

This document explains how information moves through the system: requests, authentication, tenant scoping, database access, analysis, CSV ingestion, and configuration. It contains no file-tree diagrams.

## 1. System context

```mermaid
flowchart LR
    U[Browser] -->|HTML navigation| P[Flask pages blueprint]
    U -->|JSON over HTTPS| A[Flask API blueprints]
    P --> APP[Flask application]
    A --> APP
    APP --> DB["MySQL database"]
    APP --> LOG[Rotating log file]
    U -.->|loads assets| CDN[Chart.js and Inter font CDN]
    ENV[Environment variables or .env] --> APP
```

The browser loads server-rendered HTML from the pages blueprint and then calls the JSON API directly with the stored bearer token. The Flask application is the only component that talks to MySQL. All persistence, tenant checks, and calculations happen server-side.

## 2. Request lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant F as Flask app
    participant G as require_auth
    participant S as Schema validator
    participant V as Service
    participant R as Repository
    participant D as MySQL

    B->>F: HTTP request
    F->>F: before_request enforce_origin
    alt Origin header present and not allowed
        F-->>B: 403 origin not allowed
    end

    alt Protected API route
        F->>G: Authorization Bearer token
        G->>G: decode JWT with SECRET_KEY
        G->>R: find user by payload.sub
        R->>D: SELECT users WHERE id = sub
        D-->>R: user row
        R-->>G: user
        G->>G: store user on Flask g.current_user
    end

    F->>S: parse JSON object and validate fields
    S-->>F: cleaned payload or ValidationError
    F->>V: execute business operation
    V->>R: tenant-scoped query
    R->>D: SQL filtered by institution_id
    D-->>R: rows
    R-->>V: model objects
    V-->>F: serialized dict or model
    F-->>B: JSON success or error envelope
    F->>D: teardown removes SQLAlchemy session
```

The invariant is one commit per request and one session cleanup per application context teardown. Services call repositories; blueprints never query the ORM directly.

## 3. Authentication and session flow

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant API as Auth blueprint
    participant AS as Auth service
    participant UR as User repository
    participant DB as MySQL

    rect rgb(240, 248, 255)
    Note over B,DB: Registration
    B->>API: POST /api/auth/register-institution
    API->>API: validate institution_name, admin_name, admin_email, password
    API->>AS: register_institution(payload)
    AS->>UR: find_by_email(admin_email)
    UR->>DB: SELECT users WHERE email = admin_email
    DB-->>UR: none
    AS->>AS: hash password with bcrypt
    AS->>DB: INSERT institution and admin user in one transaction
    AS->>AS: create JWT with sub, institution_id, role, iat, exp
    AS-->>API: institution_id, user_id, access_token, token_type
    API-->>B: 201 success envelope
    end

    rect rgb(245, 255, 245)
    Note over B,DB: Login
    B->>API: POST /api/auth/login
    API->>AS: login(payload)
    AS->>UR: find_by_email(email)
    UR->>DB: SELECT users WHERE email = email
    DB-->>UR: user row
    AS->>AS: bcrypt check password
    AS->>AS: create JWT
    AS-->>API: access_token, token_type, user summary
    API-->>B: 200 success envelope
    end

    rect rgb(255, 250, 240)
    Note over B,DB: Authenticated request
    B->>API: GET /api/auth/session with Authorization Bearer token
    API->>API: require_auth decodes JWT
    API->>UR: find_by_id(payload.sub)
    UR->>DB: SELECT users WHERE id = sub
    DB-->>UR: user
    API-->>B: user summary including institution_name
    end
```

The token payload is:

```json
{
  "sub": "1",
  "institution_id": "1",
  "role": "admin",
  "iat": 1760000000,
  "exp": 1760003600
}
```

The token is signed with HS256 using `SECRET_KEY`, which is populated from `JWT_SECRET`. The browser stores the token under `energy_audit_token` and sends it as `Authorization: Bearer <token>`. The server never uses cookies for identity.

## 4. Tenant isolation flow

```mermaid
flowchart TD
    J[JWT payload] --> I[institution_id from token]
    I --> Q[Every repository query adds institution filter]
    Q --> BQ[buildings WHERE institution_id = token institution_id]
    Q --> UQ[users WHERE institution_id = token institution_id]
    Q --> EQ[energy_records WHERE institution_id = token institution_id]
    BQ --> M{row exists and matches?}
    UQ --> M
    EQ --> M
    M -->|yes| OK[return serialized data]
    M -->|no| NF[404 Not Found]
```

Two database constraints enforce the same rule structurally:

- `buildings` has a unique key on `(institution_id, id)`.
- `energy_records` has a composite foreign key from `(institution_id, building_id)` to `buildings(institution_id, id)`.

The scope always comes from the JWT. URL parameters and request bodies never supply `institution_id`. Cross-tenant access therefore looks identical to a missing row: the server returns 404 rather than revealing that the row exists elsewhere.

## 5. Data model

```mermaid
erDiagram
    INSTITUTIONS ||--o{ USERS : contains
    INSTITUTIONS ||--o{ BUILDINGS : contains
    BUILDINGS ||--o{ ENERGY_RECORDS : records

    INSTITUTIONS {
        bigint id PK
        string name UK
        string currency
        int max_buildings
        datetime created_at
    }

    USERS {
        bigint id PK
        bigint institution_id FK
        string name
        string email UK
        string password_hash
        string role
        boolean must_change_password
        datetime created_at
    }

    BUILDINGS {
        bigint id PK
        bigint institution_id FK
        string name
        string type
        decimal floor_area_m2
        int operating_hours
    }

    ENERGY_RECORDS {
        bigint id PK
        bigint institution_id FK
        bigint building_id FK
        date month
        decimal kwh
        decimal cost
    }
```

Important column semantics:

- `energy_records.month` stores the first day of the month. The API always exposes it as `YYYY-MM`.
- `energy_records` is unique on `(building_id, month)`, so a building cannot have two records for the same month.
- `buildings` is unique on `(institution_id, name)` and on `(institution_id, id)`.
- `users.email` is globally unique.
- `buildings.floor_area_m2` must be greater than 0.
- `buildings.operating_hours` must be between 1 and 24.
- `energy_records.kwh` and `energy_records.cost` must be greater than or equal to 0.
- Deleting an institution cascades to users and buildings; deleting a building cascades to its energy records.

## 6. Analysis pipeline

```mermaid
flowchart LR
    ER[energy_records for one building] --> AK[annual_kwh = sum kwh]
    ER --> AC[annual_cost = sum cost]
    ER --> MS[monthly_series]
    ER --> EU[eui = total_kwh / floor_area_m2]
    ER --> AN[anomaly_months]

    AK --> BA[building analysis payload]
    AC --> BA
    MS --> BA
    EU --> BA
    AN --> BA
    BA --> RESP1[GET /buildings/id/analysis]

    BA --> CMP[compare_buildings]
    CMP --> TYP{more than one building type?}
    TYP -->|yes| WARN[warning string]
    TYP -->|no| NOWARN[warning null]
    CMP --> RESP2[GET /analysis/compare]

    ER --> AGG[aggregation_by_month]
    AGG --> DS[dashboard summary]
    AK --> DS
    AC --> DS
    AN --> DS
    DS --> RESP3[GET /dashboard]
```

The analysis module is intentionally pure: it receives lists of model objects or dictionaries and returns plain dictionaries. It does not query the database. The dashboard service is the orchestration layer that fetches data, calls the pure functions, and assembles the response.

## 7. CSV import flow

```mermaid
flowchart TD
    IN[POST csv text and confirm flag] --> EMPTY{csv non-empty?}
    EMPTY -->|no| E0[error row 0: CSV is empty]
    EMPTY -->|yes| HDR{header equals month,kwh,cost?}
    HDR -->|no| E1[error row 1: invalid header]
    HDR -->|yes| LOOP[iterate data rows]

    LOOP --> BLANK{blank row?}
    BLANK -->|yes| SKIP[skip row]
    BLANK -->|no| CELLS{at least 3 cells?}
    CELLS -->|no| EROW[append row error]
    CELLS -->|yes| PARSE[parse month, kwh, cost]

    PARSE --> MONTH{month matches YYYY-MM?}
    MONTH -->|no| EROW
    MONTH -->|yes| NUM{kwh and cost are numbers and non-negative?}
    NUM -->|no| EROW
    NUM -->|yes| DUPFILE{duplicate month in file?}
    DUPFILE -->|yes| EROW
    DUPFILE -->|no| DUPDB{month already in database?}
    DUPDB -->|yes| EROW
    DUPDB -->|no| VALID[append to valid rows]

    EROW --> ERR[errors list]
    VALID --> CONFIRM{confirm is true?}
    ERR --> CONFIRM
    SKIP --> CONFIRM

    CONFIRM -->|no| DRY[return valid_rows, errors, imported 0, requires_confirmation true]
    CONFIRM -->|yes| INSERT[insert valid rows only, commit once]
    INSERT --> DONE[return valid_rows, errors, imported count]
```

The parser is a pure utility. The service adds the database-existence check, sorts errors by row number, and only writes when `confirm` is true. Invalid rows never block valid rows from importing.

## 8. Frontend session gate

```mermaid
flowchart TD
    START([Page load]) --> TOKEN{"Token in localStorage?"}
    TOKEN -->|"no, dashboard page"| LOGIN["Redirect to login"]
    TOKEN -->|"no, public page"| SHELL["Render public shell"]
    TOKEN -->|"yes"| SESSION["Call session endpoint"]
    SESSION -->|"fails"| CLEAR["Clear token and redirect to login"]
    SESSION -->|"valid on auth page"| DASH["Redirect to dashboard"]
    SESSION -->|"valid on app page"| APP["Render app page"]
    SHELL -->|"user submits login"| LOGIN
    LOGIN -->|"token stored"| APP
    APP -->|"logout"| CLEAR
```

The HTML pages are public shells. The server does not redirect unauthenticated HTML requests; it returns the page and the client JavaScript performs the gate. This avoids a redirect loop caused by browser navigation not carrying the bearer token. Actual data protection still happens on every API call through `require_auth`.

## 9. Configuration and startup flow

```mermaid
flowchart TD
    DOTENV[".env file"] --> ENV["Process environment"]
    OSENV["Operating system environment"] --> ENV
    ENV --> CFG["server.config"]

    CFG --> URL["build_database_url"]
    URL --> URI["SQLALCHEMY_DATABASE_URI"]
    ENV --> JWTSEC["JWT_SECRET"]
    ENV --> JWTEXP["JWT_EXPIRATION_SECONDS"]
    ENV --> BCRYPT["BCRYPT_ROUNDS"]
    ENV --> CORS["CORS_ORIGINS"]
    ENV --> LOGLEVEL["LOG_LEVEL"]

    URI --> FACTORY["create_app"]
    JWTSEC --> FACTORY
    JWTEXP --> FACTORY
    BCRYPT --> FACTORY
    CORS --> FACTORY
    LOGLEVEL --> FACTORY

    FACTORY --> EXT["Initialize SQLAlchemy"]
    FACTORY --> HANDLERS["Register error handlers and logger"]
    FACTORY --> BPS["Register API and page blueprints"]
    FACTORY --> GUARD["Register origin backstop and teardown"]
    EXT --> MYSQL["MySQL database"]
    HANDLERS --> LOGFILE["logs/energy_audit.log"]
```

`MYSQL_PORT` is omitted from the SQLAlchemy URI when the environment variable is empty. That keeps managed hosts such as PythonAnywhere from receiving `host:` with a blank port and raising `ValueError`. If `MYSQL_PORT` is set, it is appended as `host:port`.

## 10. Key invariants

- Identity always comes from the bearer token, never from a cookie, URL, or request body.
- Every tenant-owned query is filtered by the token's `institution_id`.
- Cross-tenant resources return 404, not 403.
- Success responses use `status: "success"`; error responses use a numeric `status` equal to the HTTP status code.
- Request bodies must be JSON objects. Non-JSON bodies and JSON arrays are rejected with 400.
- Only the register-institution and login endpoints are public. Every other API endpoint requires a bearer token.
- Roles are enforced with `require_role` on the server. Admin-only endpoints are user management and institution updates.
- All database writes are committed once per request by the service layer.
- Analysis functions are pure and unit-testable without a database.
