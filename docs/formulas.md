# Formulas — What the Backend Does With Input

Related docs: [Architecture](architecture.md) · [API reference](api.md) · [What has been built](what-has-been-built.md)

This document describes the calculations and transformations performed after data is validated.

## 1. Inputs and units

| Input | Unit | Constraint |
|-------|------|------------|
| `month` | `YYYY-MM` | Month 01–12; stored as first day of month |
| `kwh` | kilowatt-hours | Numeric, >= 0 |
| `cost` | institution currency | Numeric, >= 0; supplied directly or auto-calculated by the UI from the standard rate |
| `floor_area_m2` | square metres | Numeric, > 0 |
| `operating_hours` | hours/day | Integer, 1–24 |

The backend does not estimate missing months. It sums exactly the records that exist.

The energy records UI auto-calculates a cost when the cost field is left blank:

```text
suggested_cost = round(kwh * institution.standard_cost_per_kwh, 2)
```

The calculated value is submitted as the stored `cost`, so analysis and dashboard totals continue to use the same `cost` field. The institution standard rate defaults to `21.84` and is editable by an admin in Settings. CSV imports still require an explicit `cost` column.

## 2. Annual totals

For records `R`:

```text
annual_kwh  = round(sum(r.kwh for r in R), 2)
annual_cost = round(sum(r.cost for r in R), 2)
```

"Annual" is historical naming. The result is the sum of all records, even if fewer than 12 months exist. There is no annualization or pro-rating.

## 3. Monthly series

One entry per record:

```text
monthly_series = [(month(r), r.kwh, r.cost) for r in R]
```

API shape:

```json
[
  { "month": "2025-01", "kwh": 1000.0, "cost": 2000.0 },
  { "month": "2025-02", "kwh": 1100.0, "cost": 2200.0 }
]
```

Records are ordered by month before this step, so the series is chronological. Individual values are converted to floats but not rounded here.

## 4. EUI and completeness

```text
EUI = round(annual_kwh / floor_area_m2, 2)
```

If `floor_area_m2` is missing or <= 0, EUI is `null`. The database check constraint prevents non-positive floor areas, so this is normally unreachable.

Completeness:

```text
eui_note = "complete"     if months >= 12
           "partial"      if months >= 6
           "insufficient" if months < 6
```

Actual behavior: EUI is calculated for any non-empty set of records, regardless of `eui_note`. A building with 3 months still gets a numeric EUI and `eui_note: "insufficient"`. The frontend should use `eui_note` to label or filter provisional EUI.

## 5. Anomaly detection

Threshold constant:

```text
ANOMALY_THRESHOLD = 0.30
```

For each record `i`, average all the other records:

```text
average_other_i = round(sum(kwh_j for j != i) / (n - 1), 2)
```

Flag as an anomaly when:

```text
kwh_i > average_other_i * (1 + 0.30)
```

The comparison is strict `>`, not `>=`.

Percent above baseline:

```text
percent_above_i = round((kwh_i - average_other_i) / average_other_i * 100, 2)
```

Anomaly payload:

```json
{
  "month": "2025-03",
  "kwh": 1500.0,
  "average_other_months": 1050.0,
  "percent_above": 42.86
}
```

Notes:

- With one record, the average is `None`, so no anomaly is produced.
- With two records, each is compared against the other single record.
- The record being tested is excluded from its own baseline.
- If all other months have `kwh = 0` and the current month is positive, the average is `0`, the threshold test succeeds, and `percent_above` divides by zero. The current code does not guard this edge case.

## 6. Dashboard monthly aggregation

Group all records from all buildings by month:

```text
aggregated(m).kwh  = sum(r.kwh for r in records where month(r) == m)
aggregated(m).cost = sum(r.cost for r in records where month(r) == m)
```

Sort by month ascending and round each total to 2 decimals:

```text
monthly_series = [
  { month: m, kwh: round(aggregated(m).kwh, 2), cost: round(aggregated(m).cost, 2) }
  for m in sorted(months)
]
```

This is an aggregation across buildings, so one month may combine several buildings.

## 7. Comparison warning

Let `T` be the set of building types included in the comparison.

```text
warning = "Comparison may not be fair because building types differ between buildings."
          if len(T) > 1
          else null
```

Two endpoints use different building sets:

- `GET /api/analysis/compare` passes every building in the institution.
- `GET /api/dashboard` builds the warning from the buildings included in `comparisons`.

## 8. Dashboard assembly

| Field | Source |
|-------|--------|
| `building_count` | number of buildings in the institution |
| `total_kwh` | sum of `annual_kwh` for every building |
| `total_cost` | sum of `annual_cost` for every building |
| `monthly_series` | aggregation across all buildings, sorted by month |
| `comparisons` | per-building analysis objects, keyed `building_id` |
| `anomalies` | flattened: `building_id`, `month`, `percent_above` |
| `warning` | type-count rule applied to `comparisons` |

Dashboard totals include buildings with incomplete data. `eui_note` communicates completeness.

Per-building comparison object:

```json
{
  "building_id": 10,
  "name": "Head Office",
  "type": "office",
  "floor_area_m2": 1200.5,
  "total_kwh": 3600.0,
  "total_cost": 7200.0,
  "monthly_records": [
    { "month": "2025-01", "kwh": 1000.0, "cost": 2000.0 }
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
```

`GET /api/analysis/compare` uses the same fields but renames `building_id` to `id`.

## 9. CSV ingestion

Order of operations:

1. **Empty check.** Empty or whitespace-only CSV returns `valid_rows: 0` and one error with `row: 0`, message `CSV is empty`.
2. **Header check.** First row, trimmed and lowercased, must equal `month,kwh,cost`. Otherwise return one error with `row: 1`, message `header must be month,kwh,cost`.
3. **Row parsing.** Data rows start at row number `2`.
   - Skip rows where every cell is blank.
   - Fewer than 3 cells produces `row must have month,kwh,cost`.
4. **Month parsing.** Must be `YYYY-MM` with month `01`–`12`. Invalid values add `month must be YYYY-MM`.
5. **Numeric parsing.** Parse `kwh` and `cost` with `Decimal`.
   - Non-numeric adds `kwh must be a number` or `cost must be a number`.
   - Negative adds `kwh must not be negative` or `cost must not be negative`.
6. **Duplicate month in file.** Track the first row per month. A repeat adds `duplicate month in file (also row N)`.
7. **Duplicate month in database.** If a record exists for that building and month, add `month already recorded for this building` and exclude the row from valid rows.
8. **Error ordering.** Sort all errors by row number.
9. **Dry run (`confirm: false`).** Return `valid_rows`, `errors`, `imported: 0`, `requires_confirmation: true`. Write nothing.
10. **Confirm (`confirm: true`).** Insert every valid row, commit once, set `imported` to the number inserted.

Row numbering:

| Situation | Row number |
|-----------|------------|
| Empty CSV | 0 |
| Invalid header | 1 |
| First data row | 2 |
| Second data row | 3 |

## 10. Authentication math

JWT payload:

```text
sub            = str(user.id)
institution_id = str(user.institution_id)
role           = user.role
iat            = current UTC time
exp            = iat + JWT_EXPIRATION_SECONDS
```

Default lifetime is 3600 seconds. Expired tokens return `401 Token expired`; malformed or wrongly signed tokens return `401 Invalid token`.

Password hashing:

```text
password_hash = bcrypt(password, rounds = BCRYPT_ROUNDS)
```

Default bcrypt rounds: 12. Password minimum length: 8 characters on registration, user creation, and password change. Login only verifies the supplied password; it does not enforce a minimum length.

## 11. Limits and defaults

| Rule | Value |
|------|-------|
| Institution default currency | `KES` |
| Institution default max buildings | 5 |
| Institution max buildings allowed | 1–50 |
| Max buildings cannot be lowered below | current building count |
| Password minimum length | 8 |
| Email uniqueness | global |
| Building name uniqueness | per institution |
| Building floor area | > 0 |
| Building operating hours | 1–24 |
| Energy month uniqueness | per building |
| Energy kWh | >= 0 |
| Energy cost | >= 0 |
| Currency format | exactly 3 alphabetic characters, stored uppercase |
| JWT lifetime default | 3600 seconds |
| Bcrypt rounds default | 12 |

Validation treats `null`, missing keys, and empty strings as missing for required fields. For example, `{"email": ""}` is reported as a missing `email`.

## 12. Numeric semantics

- Database columns `floor_area_m2`, `kwh`, and `cost` use fixed-point `NUMERIC` types.
- The API converts them to JavaScript-safe floats.
- Calculations use Python `float` for sums and ratios, then `round(value, 2)`.
- Python `round` uses round-half-to-even, not round-half-up.
- Percentages are rounded to 2 decimals.
- The API values are the canonical values; the frontend may add display formatting.

## 13. Worked example

Building:

```json
{
  "name": "Head Office",
  "type": "office",
  "floor_area_m2": 1200.5,
  "operating_hours": 10
}
```

Records:

| Month | kWh | Cost |
|-------|-----|------|
| 2025-01 | 1000 | 2000 |
| 2025-02 | 1100 | 2200 |
| 2025-03 | 1500 | 3000 |

Annual totals:

```text
annual_kwh  = 1000 + 1100 + 1500 = 3600.00
annual_cost = 2000 + 2200 + 3000 = 7200.00
```

EUI:

```text
EUI = round(3600 / 1200.5, 2)
    = round(2.99875, 2)
    = 3.00
```

Completeness: 3 records, so `eui_note = "insufficient"`.

Anomaly detection:

| Month | kWh | Average of others | Threshold at 1.30x | Anomaly? | Percent above |
|-------|-----|-------------------|--------------------|----------|---------------|
| 2025-01 | 1000 | (1100 + 1500) / 2 = 1300.00 | 1690.00 | no | — |
| 2025-02 | 1100 | (1000 + 1500) / 2 = 1250.00 | 1625.00 | no | — |
| 2025-03 | 1500 | (1000 + 1100) / 2 = 1050.00 | 1365.00 | yes | (1500 - 1050) / 1050 × 100 = 42.86 |

Result:

```json
[
  {
    "month": "2025-03",
    "kwh": 1500.0,
    "average_other_months": 1050.0,
    "percent_above": 42.86
  }
]
```

If this were the only building, `warning` is `null` because there is only one distinct building type.

## 14. Formula summary

```text
annual_kwh      = round(sum(record.kwh), 2)
annual_cost     = round(sum(record.cost), 2)
EUI             = round(annual_kwh / floor_area_m2, 2)

eui_note        = "complete"     if months >= 12
                  "partial"      if months >= 6
                  "insufficient" if months < 6

average_other_i = round(sum(kwh_j for j != i) / (n - 1), 2)
is_anomaly_i    = kwh_i > average_other_i * 1.30
percent_above_i = round((kwh_i - average_other_i) / average_other_i * 100, 2)

aggregate_month(m).kwh  = round(sum(kwh of month m), 2)
aggregate_month(m).cost = round(sum(cost of month m), 2)

warning         = true if the set of building types has more than one type

token_exp       = token_iat + JWT_EXPIRATION_SECONDS
password_hash   = bcrypt(password, BCRYPT_ROUNDS)
```

## 15. Known calculation gaps

- No annualization or pro-rating for partial years.
- No weather normalization.
- No carbon or solar estimation.
- No tariff model beyond a single institution-level standard cost per kWh; no time-of-use, demand charges, or tiered tariffs.
- No anomaly guard for a zero baseline.
- EUI is numeric even when `eui_note` is `partial` or `insufficient`.
