# API Reference — Energy Audit App

All routes are under `/api`. All routes require authentication except `POST /auth/register-institution` and `POST /auth/login`.

## Error format
```json
{ "status": 400, "message": "...", "errors": {} }
```

## Auth
### `POST /auth/register-institution`
Body: `{ institution_name, admin_name, admin_email, password }` (password min 8 chars)
Creates institution + first admin. Returns `{ institution_id, user_id, access_token, token_type }`.

### `POST /auth/login`
Body: `{ email, password }`
Returns `{ access_token, token_type, user: { id, institution_id, role, must_change_password } }`.

### `POST /auth/logout`
Requires `Authorization: Bearer <token>`. Returns `{ status: "success", message: "Logged out" }`.

### `POST /auth/change-password`
Requires auth. Body: `{ current_password, new_password }`.

### `GET /auth/session`
Requires auth. Returns current user summary: `{ id, institution_id, institution_name, email, role, must_change_password }`.

## Institution
### `GET /institution`
Returns `{ name, currency, max_buildings }`.

### `PATCH /institution` (admin only)
Body: `{ name?, currency?, max_buildings? }`. `max_buildings` must be 1–50 and >= current building count.

## Users (admin only)
### `GET /users`
List users for the institution.

### `POST /users`
Body: `{ name, email, password, role }`. Creates auditor/admin with temp password (`must_change_password=true`).

### `PATCH /users/<user_id>` (admin only)
Update user fields.

### `DELETE /users/<user_id>` (admin only)
Cannot delete self.

## Buildings
### `GET /buildings`
List institution's buildings.

### `POST /buildings`
Body: `{ name, type, floor_area_m2, operating_hours }`. Enforces `max_buildings`. Name unique per institution.

### `GET /buildings/<id>`
### `PATCH /buildings/<id>`
### `DELETE /buildings/<id>`

Cross-tenant access returns 404.

## Energy records
### `GET /buildings/<id>/energy`
List records for a building (sorted by month).

### `POST /buildings/<id>/energy`
Body: `{ month (YYYY-MM), kwh (>=0), cost (>=0) }`. Month must be unique per building.

### `POST /buildings/<id>/energy/import`
Body: `{ csv: "month,kwh,cost\n...", confirm: bool }`.
- `confirm: false` → dry run: returns `{ valid_rows, errors, imported: 0, requires_confirmation: true }`.
- `confirm: true` → imports valid rows only; invalid rows reported with row numbers.

### `PATCH /buildings/<id>/energy/<recId>`
Update month/kwh/cost.

### `DELETE /buildings/<id>/energy/<recId>`

## Analysis
### `GET /buildings/<id>/analysis`
Returns annual totals, EUI (complete only with 12 months), monthly series, anomaly flags (>30% above average of other months).

### `GET /analysis/compare`
Compare buildings by EUI within the institution. Warns if building types differ.

### `GET /dashboard`
Institution summary: building count, total kWh, total cost, monthly series aggregated across buildings, comparisons, anomalies.

## Responses
Success: `{ "status": "success", "message": "...", "data": {...} }`
