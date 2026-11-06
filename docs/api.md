# API Reference — Energy Audit App

Related docs: [Architecture](architecture.md) · [Formulas](formulas.md) · [What has been built](what-has-been-built.md)

This document is the complete contract needed to build a frontend against the API without reading the server code. Every request and response shape below matches the current implementation.

## 1. Conventions

### Base URL
All API routes are relative to the same origin that serves the HTML pages:

```text
https://your-host/api/...
```

### Content type
`POST` and `PATCH` requests that carry a body must use:

```http
Content-Type: application/json
```

The body must be a JSON object. A JSON array, a missing body, or a non-JSON content type returns `400`.

### Authentication
Every API endpoint except registration and login requires:

```http
Authorization: Bearer <access_token>
```

There is no cookie-based authentication and no refresh token. The default token lifetime is 3600 seconds, configurable with `JWT_EXPIRATION_SECONDS`.

### Success envelope
```json
{
  "status": "success",
  "message": "Human readable message",
  "data": {}
}
```

`status` is the string `"success"` on success. `data` may be `null`. `meta` is only present when a handler supplies it; current handlers do not.

### Error envelope
```json
{
  "status": 400,
  "message": "Human readable message",
  "errors": {
    "field": ["reason"]
  }
}
```

`status` is a number equal to the HTTP status code on error.

### Status codes

| HTTP | Meaning | Typical cause |
|------|---------|---------------|
| 200 | OK | Successful read, update, delete, or login |
| 201 | Created | Institution, user, building, or energy record created |
| 400 | Bad Request | Missing fields, wrong type, invalid month, invalid JSON |
| 401 | Unauthorized | Missing/expired/invalid token, bad login, wrong current password |
| 403 | Forbidden | Wrong role, or disallowed `Origin` header |
| 404 | Not Found | Resource missing or belongs to another institution |
| 405 | Method Not Allowed | Route exists but method is wrong |
| 409 | Conflict | Duplicate email/name/month, building limit, self-delete |
| 500 | Internal Server Error | Unhandled exception |

### Origin guard
If a request contains an `Origin` header, the value must appear in the `CORS_ORIGINS` environment variable (comma-separated) or the server returns:

```json
{
  "status": 403,
  "message": "origin not allowed",
  "errors": {}
}
```

Browsers may send `Origin` on non-GET requests even for same-origin calls. To use the frontend from a browser, include the app's own origin in `CORS_ORIGINS`, for example:

```text
CORS_ORIGINS=http://localhost:5000,https://your-host
```

### Common validation error
Missing required fields:

```json
{
  "status": 400,
  "message": "Missing required fields",
  "errors": {
    "fields": ["email", "password"]
  }
}
```

Non-JSON body:

```json
{
  "status": 400,
  "message": "Content-Type must be application/json",
  "errors": {
    "body": ["request body must be JSON"]
  }
}
```

---

## 2. Authentication

### 2.1 Register institution

`POST /api/auth/register-institution` — public

Creates an institution and its first admin user in one transaction. The admin is created with `role: "admin"` and `must_change_password: true`.

Request:
```json
{
  "institution_name": "Acme Corp",
  "admin_name": "Jane Doe",
  "admin_email": "jane@acme.com",
  "password": "secret123"
}
```

Response `201`:
```json
{
  "status": "success",
  "message": "Institution created",
  "data": {
    "institution_id": 1,
    "user_id": 1,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer"
  }
}
```

Errors:

| HTTP | message | errors |
|------|---------|--------|
| 400 | Missing required fields | `{"fields": [...]}` |
| 400 | password must be at least 8 characters | `{"password": ["min length is 8"]}` |
| 409 | Email already registered | `{"email": ["already in use"]}` |

The frontend should store `data.access_token` and navigate to `/dashboard`.

### 2.2 Login

`POST /api/auth/login` — public

Request:
```json
{
  "email": "jane@acme.com",
  "password": "secret123"
}
```

Response `200`:
```json
{
  "status": "success",
  "message": "Authenticated",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "user": {
      "id": 1,
      "institution_id": 1,
      "role": "admin",
      "must_change_password": true
    }
  }
}
```

Error `401`:
```json
{
  "status": 401,
  "message": "Invalid email or password",
  "errors": {}
}
```

Passwords are compared case-sensitively after email is trimmed and lowercased.

### 2.3 Logout

`POST /api/auth/logout` — bearer required

No request body is required. The server does not maintain a token blacklist, so logout is a client-side token removal. The endpoint exists so the frontend can make an explicit call.

Response `200`:
```json
{
  "status": "success",
  "message": "Logged out",
  "data": null
}
```

### 2.4 Change password

`POST /api/auth/change-password` — bearer required

Request:
```json
{
  "current_password": "secret123",
  "new_password": "newsecret456"
}
```

Success `200`:
```json
{
  "status": "success",
  "message": "Password changed",
  "data": null
}
```

Errors:

| HTTP | message | errors |
|------|---------|--------|
| 400 | Missing required fields | `{"fields": [...]}` |
| 400 | new_password must be at least 8 characters | `{"new_password": ["min length is 8"]}` |
| 401 | Current password is incorrect | `{}` |

On success, `must_change_password` becomes `false`.

### 2.5 Session

`GET /api/auth/session` — bearer required

This is the canonical endpoint for restoring the frontend session after a page load.

Response `200`:
```json
{
  "status": "success",
  "message": "Session",
  "data": {
    "user": {
      "id": 1,
      "institution_id": 1,
      "institution_name": "Acme Corp",
      "email": "jane@acme.com",
      "role": "admin",
      "must_change_password": false
    }
  }
}
```

A `401` means the token is missing, expired, or invalid. The frontend should clear its stored token and redirect to `/login`.

---

## 3. Institution

### 3.1 Get institution

`GET /api/institution` — bearer required, any role

Response `200`:
```json
{
  "status": "success",
  "message": "Institution fetched",
  "data": {
    "id": 1,
    "name": "Acme Corp",
    "currency": "KES",
    "max_buildings": 5,
    "created_at": "2026-01-15T09:30:00+00:00"
  }
}
```

`currency` is a three-letter uppercase code. It controls how the frontend should format cost values.

### 3.2 Update institution

`PATCH /api/institution` — bearer + admin role

All fields are optional, but at least one should be sent. An empty object returns the unchanged institution.

Request:
```json
{
  "name": "Acme Holdings",
  "currency": "USD",
  "max_buildings": 10
}
```

Response `200`:
```json
{
  "status": "success",
  "message": "Institution updated",
  "data": {
    "id": 1,
    "name": "Acme Holdings",
    "currency": "USD",
    "max_buildings": 10,
    "created_at": "2026-01-15T09:30:00+00:00"
  }
}
```

Validation and business errors:

| HTTP | message | errors |
|------|---------|--------|
| 400 | name must be a non-empty string | `{"name": ["required"]}` |
| 400 | currency must be a 3-letter code | `{"currency": ["must be a 3-letter code"]}` |
| 400 | max_buildings must be an integer | `{"max_buildings": ["must be an integer"]}` |
| 400 | max_buildings must be between 1 and 50 | `{"max_buildings": ["must be 1..50"]}` |
| 403 | Forbidden | `{}` when the caller is an auditor |
| 409 | Institution name already in use | `{"name": ["already in use"]}` |
| 409 | Building limit cannot be below the current building count | `{"max_buildings": ["current building count is N"]}` |

---

## 4. Users

All user endpoints are admin-only. Auditors receive `403 Forbidden`.

### 4.1 List users

`GET /api/users` — bearer + admin

Response `200`:
```json
{
  "status": "success",
  "message": "Users fetched",
  "data": [
    {
      "id": 1,
      "institution_id": 1,
      "name": "Jane Doe",
      "email": "jane@acme.com",
      "role": "admin",
      "must_change_password": false,
      "created_at": "2026-01-15T09:30:00+00:00"
    },
    {
      "id": 2,
      "institution_id": 1,
      "name": "John Auditor",
      "email": "john@acme.com",
      "role": "auditor",
      "must_change_password": true,
      "created_at": "2026-02-01T08:00:00+00:00"
    }
  ]
}
```

Users are ordered by name.

### 4.2 Create user

`POST /api/users` — bearer + admin

Request:
```json
{
  "name": "John Auditor",
  "email": "john@acme.com",
  "password": "temp1234"
}
```

Response `201`:
```json
{
  "status": "success",
  "message": "User created",
  "data": {
    "id": 2,
    "institution_id": 1,
    "name": "John Auditor",
    "email": "john@acme.com",
    "role": "auditor",
    "must_change_password": true,
    "created_at": "2026-02-01T08:00:00+00:00"
  }
}
```

**Important:** the server ignores any `role` field in the request body. Every created user is an `auditor`. The current UI shows a role selector, but the backend hardcodes `role="auditor"`.

Errors:

| HTTP | message | errors |
|------|---------|--------|
| 400 | Missing required fields | `{"fields": [...]}` |
| 400 | email must be valid | `{"email": ["invalid email"]}` |
| 400 | password must be at least 8 characters | `{"password": ["min length is 8"]}` |
| 403 | Forbidden | `{}` |
| 409 | Email already registered | `{"email": ["already in use"]}` |

### 4.3 Update user

`PATCH /api/users/<user_id>` — bearer + admin

Only `name` and `password` are accepted. Sending `email` or `role` has no effect.

Request:
```json
{
  "name": "John Smith",
  "password": "newpass123"
}
```

Response `200`:
```json
{
  "status": "success",
  "message": "User updated",
  "data": {
    "id": 2,
    "institution_id": 1,
    "name": "John Smith",
    "email": "john@acme.com",
    "role": "auditor",
    "must_change_password": true,
    "created_at": "2026-02-01T08:00:00+00:00"
  }
}
```

Changing the password sets `must_change_password` back to `true`. A user from another institution returns `404`.

### 4.4 Delete user

`DELETE /api/users/<user_id>` — bearer + admin

Success `200`:
```json
{
  "status": "success",
  "message": "User deleted",
  "data": null
}
```

Errors:

| HTTP | message | errors |
|------|---------|--------|
| 404 | User not found | `{}` |
| 409 | You cannot delete your own account | `{}` |

---

## 5. Buildings

Any authenticated role can manage buildings.

### 5.1 List buildings

`GET /api/buildings` — bearer required

Response `200`:
```json
{
  "status": "success",
  "message": "Buildings fetched",
  "data": [
    {
      "id": 10,
      "institution_id": 1,
      "name": "Head Office",
      "type": "office",
      "floor_area_m2": 1200.5,
      "operating_hours": 10
    }
  ]
}
```

Buildings are ordered by name. `floor_area_m2` is a float, `operating_hours` is an integer.

### 5.2 Create building

`POST /api/buildings` — bearer required

Request:
```json
{
  "name": "Head Office",
  "type": "office",
  "floor_area_m2": 1200.5,
  "operating_hours": 10
}
```

Response `201`:
```json
{
  "status": "success",
  "message": "Building created",
  "data": {
    "id": 10,
    "institution_id": 1,
    "name": "Head Office",
    "type": "office",
    "floor_area_m2": 1200.5,
    "operating_hours": 10
  }
}
```

Suggested `type` values used by the UI: `office`, `retail`, `warehouse`, `factory`, `other`. The server accepts any non-empty string.

Errors:

| HTTP | message | errors |
|------|---------|--------|
| 400 | Missing required fields | `{"fields": [...]}` |
| 400 | floor_area_m2 must be a number | `{"floor_area_m2": ["must be a number"]}` |
| 400 | floor_area_m2 must be positive | `{"floor_area_m2": ["must be greater than 0"]}` |
| 400 | operating_hours must be between 1 and 24 | `{"operating_hours": ["must be 1..24"]}` |
| 409 | Building limit reached | `{"buildings": ["the limit is N"]}` |
| 409 | Building name already in use | `{"name": ["already in use"]}` |

### 5.3 Get building

`GET /api/buildings/<building_id>` — bearer required

Response `200` is the same single object shape as list items:

```json
{
  "status": "success",
  "message": "Building fetched",
  "data": {
    "id": 10,
    "institution_id": 1,
    "name": "Head Office",
    "type": "office",
    "floor_area_m2": 1200.5,
    "operating_hours": 10
  }
}
```

### 5.4 Update building

`PATCH /api/buildings/<building_id>` — bearer required

All fields optional. Only supplied fields change.

Request:
```json
{
  "name": "Head Office Annex",
  "type": "office",
  "floor_area_m2": 1350.0,
  "operating_hours": 12
}
```

Response `200`:
```json
{
  "status": "success",
  "message": "Building updated",
  "data": {
    "id": 10,
    "institution_id": 1,
    "name": "Head Office Annex",
    "type": "office",
    "floor_area_m2": 1350.0,
    "operating_hours": 12
  }
}
```

Errors include the same validation errors as create, plus `409 Building name already in use` and `404 Building not found`.

### 5.5 Delete building

`DELETE /api/buildings/<building_id>` — bearer required

Success `200`:
```json
{
  "status": "success",
  "message": "Building deleted",
  "data": null
}
```

Deleting a building cascades to all of its energy records. A building from another institution returns `404`.

---

## 6. Energy records

Energy records belong to one building. The building must belong to the caller's institution.

### 6.1 List energy records

`GET /api/buildings/<building_id>/energy` — bearer required

Response `200`:
```json
{
  "status": "success",
  "message": "Energy records fetched",
  "data": [
    {
      "id": 100,
      "institution_id": 1,
      "building_id": 10,
      "month": "2025-01",
      "kwh": 1000.0,
      "cost": 2000.0
    },
    {
      "id": 101,
      "institution_id": 1,
      "building_id": 10,
      "month": "2025-02",
      "kwh": 1100.0,
      "cost": 2200.0
    }
  ]
}
```

Records are ordered by month ascending. `month` is always `YYYY-MM`.

### 6.2 Create energy record

`POST /api/buildings/<building_id>/energy` — bearer required

Request:
```json
{
  "month": "2025-01",
  "kwh": 1000,
  "cost": 2000
}
```

Response `201`:
```json
{
  "status": "success",
  "message": "Energy record created",
  "data": {
    "id": 100,
    "institution_id": 1,
    "building_id": 10,
    "month": "2025-01",
    "kwh": 1000.0,
    "cost": 2000.0
  }
}
```

Errors:

| HTTP | message | errors |
|------|---------|--------|
| 400 | month must be YYYY-MM | `{"month": ["must be YYYY-MM"]}` |
| 400 | kwh must be a number | `{"kwh": ["must be a number"]}` |
| 400 | kwh must not be negative | `{"kwh": ["must be greater than or equal to 0"]}` |
| 400 | cost must be a number | `{"cost": ["must be a number"]}` |
| 400 | cost must not be negative | `{"cost": ["must be greater than or equal to 0"]}` |
| 404 | Building not found | `{}` |
| 409 | A record for that month already exists | `{"month": ["already recorded for this building"]}` |

### 6.3 Import energy records from CSV

`POST /api/buildings/<building_id>/energy/import` — bearer required

The request body contains the raw CSV text and a confirmation flag. `confirm` defaults to `false` when omitted.

Request, dry run:
```json
{
  "csv": "month,kwh,cost\n2025-01,1200,2400\n2025-02,1100,2200",
  "confirm": false
}
```

Dry-run response `200`:
```json
{
  "status": "success",
  "message": "CSV processed",
  "data": {
    "valid_rows": 2,
    "errors": [],
    "imported": 0,
    "requires_confirmation": true
  }
}
```

Confirmed request:
```json
{
  "csv": "month,kwh,cost\n2025-01,1200,2400\n2025-02,1100,2200",
  "confirm": true
}
```

Confirmed response `200`:
```json
{
  "status": "success",
  "message": "CSV processed",
  "data": {
    "valid_rows": 2,
    "errors": [],
    "imported": 2
  }
}
```

Response with row errors:
```json
{
  "status": "success",
  "message": "CSV processed",
  "data": {
    "valid_rows": 1,
    "errors": [
      {
        "row": 3,
        "message": "month must be YYYY-MM; kwh must not be negative"
      },
      {
        "row": 4,
        "message": "month already recorded for this building"
      }
    ],
    "imported": 1
  }
}
```

CSV rules:

| Rule | Behavior |
|------|----------|
| Empty CSV | error with `row: 0`, message `CSV is empty` |
| Header | Must be exactly `month,kwh,cost` after trimming and lowercasing; otherwise error with `row: 1` |
| Data row numbering | First data row is `row: 2` |
| Blank rows | Skipped |
| Fewer than 3 cells | row error `row must have month,kwh,cost` |
| Month | Must match `YYYY-MM` with month `01`–`12` |
| kWh and cost | Must be numeric and non-negative |
| Duplicate month in file | Row error `duplicate month in file (also row N)` |
| Month already in database | Row error `month already recorded for this building` |
| Dry run | Nothing is written; `imported` is `0`; `requires_confirmation` is `true` |
| Confirm | Only valid rows are inserted; invalid rows are reported and skipped |
| Error order | Errors are sorted by row number |

CSV example:

```text
month,kwh,cost
2025-01,1200,2400
2025-02,1100,2200
2025-03,1500,3000
```

### 6.4 Update energy record

`PATCH /api/buildings/<building_id>/energy/<record_id>` — bearer required

All fields optional.

Request:
```json
{
  "month": "2025-04",
  "kwh": 1600,
  "cost": 3200
}
```

Response `200`:
```json
{
  "status": "success",
  "message": "Energy record updated",
  "data": {
    "id": 100,
    "institution_id": 1,
    "building_id": 10,
    "month": "2025-04",
    "kwh": 1600.0,
    "cost": 3200.0
  }
}
```

Changing `month` to a month already used by the same building returns `409`. A record that does not belong to the building, or a building in another institution, returns `404`.

### 6.5 Delete energy record

`DELETE /api/buildings/<building_id>/energy/<record_id>` — bearer required

Success `200`:
```json
{
  "status": "success",
  "message": "Energy record deleted",
  "data": null
}
```

Missing record or cross-tenant building returns `404`.

---

## 7. Analysis

### 7.1 Building analysis

`GET /api/buildings/<building_id>/analysis` — bearer required

Response `200`:
```json
{
  "status": "success",
  "message": "Analysis computed",
  "data": {
    "building_id": 10,
    "name": "Head Office",
    "type": "office",
    "floor_area_m2": 1200.5,
    "total_kwh": 3600.0,
    "total_cost": 7200.0,
    "monthly_records": [
      {
        "month": "2025-01",
        "kwh": 1000.0,
        "cost": 2000.0
      },
      {
        "month": "2025-02",
        "kwh": 1100.0,
        "cost": 2200.0
      },
      {
        "month": "2025-03",
        "kwh": 1500.0,
        "cost": 3000.0
      }
    ],
    "eui": 3.0,
    "eui_note": "insufficient",
    "anomalies": [
      {
        "month": "2025-03",
        "kwh": 1500.0,
        "average_other_months": 1050.0,
        "percent_above": 42.86
      }
    ]
  }
}
```

`eui_note` values:

| Value | Meaning |
|-------|---------|
| `complete` | 12 or more monthly records |
| `partial` | 6 to 11 monthly records |
| `insufficient` | fewer than 6 monthly records |

`eui` is `null` only when floor area is missing or not positive. In practice the database rejects non-positive floor area, so it is normally numeric even when `eui_note` is `partial` or `insufficient`.

Missing or cross-tenant building returns `404`.

### 7.2 Compare buildings

`GET /api/analysis/compare` — bearer required

Response `200`:
```json
{
  "status": "success",
  "message": "Building comparison",
  "data": {
    "comparisons": [
      {
        "id": 10,
        "name": "Head Office",
        "type": "office",
        "floor_area_m2": 1200.5,
        "total_kwh": 3600.0,
        "total_cost": 7200.0,
        "eui": 3.0,
        "eui_note": "insufficient"
      }
    ],
    "warning": null
  }
}
```

`warning` becomes a string when the compared buildings have more than one distinct `type`:

```json
{
  "warning": "Comparison may not be fair because building types differ between buildings."
}
```

Comparison entries use the key `id` for the building identifier. This differs from the dashboard comparison entries, which use `building_id`.

### 7.3 Dashboard

`GET /api/dashboard` — bearer required

Response `200`:
```json
{
  "status": "success",
  "message": "Dashboard summary",
  "data": {
    "institution_id": 1,
    "building_count": 1,
    "total_kwh": 3600.0,
    "total_cost": 7200.0,
    "monthly_series": [
      {
        "month": "2025-01",
        "kwh": 1000.0,
        "cost": 2000.0
      },
      {
        "month": "2025-02",
        "kwh": 1100.0,
        "cost": 2200.0
      },
      {
        "month": "2025-03",
        "kwh": 1500.0,
        "cost": 3000.0
      }
    ],
    "comparisons": [
      {
        "building_id": 10,
        "name": "Head Office",
        "type": "office",
        "floor_area_m2": 1200.5,
        "total_kwh": 3600.0,
        "total_cost": 7200.0,
        "monthly_records": [
          {
            "month": "2025-01",
            "kwh": 1000.0,
            "cost": 2000.0
          },
          {
            "month": "2025-02",
            "kwh": 1100.0,
            "cost": 2200.0
          },
          {
            "month": "2025-03",
            "kwh": 1500.0,
            "cost": 3000.0
          }
        ],
        "eui": 3.0,
        "eui_note": "insufficient",
        "anomalies": [
          {
            "month": "2025-03",
            "kwh": 1500.0,
            "average_other_months": 1050.0,
            "percent_above": 42.86
          }
        ]
      }
    ],
    "warning": null,
    "anomalies": [
      {
        "building_id": 10,
        "month": "2025-03",
        "percent_above": 42.86
      }
    ]
  }
}
```

Dashboard notes:

- `total_kwh` and `total_cost` include every building and every record, including buildings with fewer than 12 months.
- `monthly_series` aggregates all buildings by month, sorted ascending by month.
- `comparisons` contains the full per-building analysis payload, but uses `building_id` instead of `id`.
- Dashboard `anomalies` is a flattened list and only includes `building_id`, `month`, and `percent_above`. It does not include `kwh` or `average_other_months`.
- `warning` is set when the buildings included in `comparisons` have more than one distinct type.

---

## 8. HTML page routes

These routes serve frontend shells. They do not return JSON and they do not check authentication on the server. The client-side session gate performs redirects, and the API enforces authentication.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/login` | Login page |
| GET | `/register` | Institution registration page |
| GET | `/dashboard` | Dashboard shell |
| GET | `/buildings` | Buildings management page |
| GET | `/buildings/<int:building_id>/energy` | Energy records page; receives `building_id` in the template context |
| GET | `/users` | Users management page |
| GET | `/settings` | Institution settings page |
| GET | `/analysis/compare` | Building comparison page |

A request to an unknown page path returns the JSON error envelope with status `404` because the global error handlers apply to all routes.

---

## 9. Frontend reconstruction contract

Everything below is required to rebuild the frontend using only this API.

### 9.1 Browser storage

| Key | Value | Purpose |
|-----|-------|---------|
| `energy_audit_token` | JWT string | Bearer token for every API call |
| `energy_audit_theme` | `"light"` or `"dark"` | Theme preference; default is `"light"` |

The default theme is light. Do not use the operating system theme as the default.

### 9.2 Session bootstrap algorithm

Run this on every page load:

```javascript
const TOKEN_KEY = "energy_audit_token";
const token = localStorage.getItem(TOKEN_KEY);
const path = window.location.pathname;

if (!token) {
  if (path === "/dashboard") {
    window.location.href = "/login";
  }
  return;
}

const response = await fetch("/api/auth/session", {
  headers: { Authorization: `Bearer ${token}` }
});

if (!response.ok) {
  localStorage.removeItem(TOKEN_KEY);
  window.location.href = "/login";
  return;
}

const body = await response.json();
const user = body.data.user;

if (path === "/login" || path === "/register") {
  window.location.href = "/dashboard";
  return;
}
```

The server intentionally does not redirect `/dashboard` to `/login`. Do not add a server-side redirect; it causes a loop because browser navigation does not carry the bearer token.

### 9.3 Page-to-endpoint map

| Page | Data needed | Endpoints |
|------|-------------|-----------|
| `/login` | none | `POST /api/auth/login` |
| `/register` | none | `POST /api/auth/register-institution` |
| `/dashboard` | session, institution currency, dashboard summary | `GET /api/auth/session`, `GET /api/institution`, `GET /api/dashboard` |
| `/buildings` | building list and CRUD | `GET /api/buildings`, `POST /api/buildings`, `PATCH /api/buildings/<id>`, `DELETE /api/buildings/<id>` |
| `/buildings/<id>/energy` | building list, energy list and CRUD, CSV import | `GET /api/buildings`, `GET /api/buildings/<id>/energy`, `POST /api/buildings/<id>/energy`, `PATCH /api/buildings/<id>/energy/<recordId>`, `DELETE /api/buildings/<id>/energy/<recordId>`, `POST /api/buildings/<id>/energy/import` |
| `/users` | user list and CRUD | `GET /api/users`, `POST /api/users`, `PATCH /api/users/<id>`, `DELETE /api/users/<id>` |
| `/settings` | institution read and update | `GET /api/institution`, `PATCH /api/institution` |
| `/analysis/compare` | comparison table | `GET /api/analysis/compare` |

### 9.4 Role-based UI

| Capability | Admin | Auditor |
|------------|-------|---------|
| Dashboard | yes | yes |
| Buildings CRUD | yes | yes |
| Energy records CRUD | yes | yes |
| Compare | yes | yes |
| Users page and API | yes | no |
| Institution settings update | yes | no |

Hide admin-only navigation and forms for auditors. Do not rely on hiding alone; the API returns `403` for admin-only endpoints.

### 9.5 Currency formatting

Fetch `currency` from `GET /api/institution` and format cost values:

| Currency | Display |
|----------|---------|
| `KES` | `KES 1,234.56` |
| `USD` | `$1,234.56` |
| anything else | `<CODE> 1,234.56` |

Use two decimal places for money. Energy totals use one decimal place and the suffix `kWh`.

### 9.6 Dashboard rendering

Use these fields:

| UI element | Data source |
|------------|-------------|
| Total energy card | `data.total_kwh` + `" kWh"` |
| Total cost card | `data.total_cost` formatted with the institution currency |
| Monthly chart | `data.monthly_series`; x-axis `month`, y-axis `kwh` |
| Anomaly list | `data.anomalies`; display `month` and `percent_above` |
| Building count | `data.building_count` |

The current design uses a bar chart with the teal color `#168C83`, no legend, and a zero-based y-axis. Chart.js 2.9.4 is loaded from a CDN in the existing template, but any charting library can be used with the same data.

### 9.7 Energy records page behavior

1. Load buildings with `GET /api/buildings`.
2. When the user selects a building, load records with `GET /api/buildings/<id>/energy`.
3. Add a record with `POST /api/buildings/<id>/energy`.
4. Delete a record with `DELETE /api/buildings/<id>/energy/<recordId>`.
5. CSV import uses the textarea contents as the `csv` string. Always submit `confirm: false` first, show `valid_rows` and row errors, then submit again with `confirm: true` when the user confirms.

### 9.8 Error handling

Read `body.message` for user-facing errors and `body.errors` for field-level details. Every API error uses the same envelope. Do not assume `data` exists on errors.

### 9.9 Empty states

The API returns an empty array, not an error, when there are no resources:

```json
{
  "status": "success",
  "message": "Buildings fetched",
  "data": []
}
```

Buildings are ordered by name. Energy records and monthly series are ordered by month ascending. Users are ordered by name.

### 9.10 Known contract quirks

- `POST /api/users` ignores `role`; created users are always `auditor`.
- `PATCH /api/users/<id>` ignores `email` and `role`; only `name` and `password` are applied.
- Logout does not invalidate the token server-side. Clear it in browser storage.
- HTML pages are public shells; API access is still protected.
- `must_change_password` is informational; no endpoint blocks access when it is `true`.
- Compare response entries use `id`; dashboard comparison entries use `building_id`.
- There is no pagination. All list endpoints return the full set.
- There is no refresh token. When the token expires, the frontend must send the user back to `/login`.
