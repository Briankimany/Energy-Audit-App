import csv
import io
from decimal import Decimal, InvalidOperation

from server.utils.dates import parse_month

REQUIRED_COLUMNS = ["month", "kwh", "cost"]


def parse_energy_csv(text: str):
    if not isinstance(text, str) or not text.strip():
        return [], [{"row": 0, "message": "CSV is empty"}]

    records = list(csv.reader(io.StringIO(text)))
    if not records:
        return [], [{"row": 0, "message": "CSV is empty"}]

    header = [cell.strip().lower() for cell in records[0]]
    if header != REQUIRED_COLUMNS:
        return [], [{"row": 1, "message": "header must be month,kwh,cost"}]

    parsed = []
    errors = []
    seen_months = {}

    for row_number, cells in enumerate(records[1:], start=2):
        if not any(cell.strip() for cell in cells):
            continue
        if len(cells) < 3:
            errors.append({"row": row_number, "message": "row must have month,kwh,cost"})
            continue

        month_raw, kwh_raw, cost_raw = (cells[0].strip(), cells[1].strip(), cells[2].strip())
        issues = []

        month = None
        try:
            month = parse_month(month_raw)
        except ValueError:
            issues.append("month must be YYYY-MM")

        kwh = None
        try:
            kwh = Decimal(kwh_raw)
            if kwh < 0:
                issues.append("kwh must not be negative")
        except (InvalidOperation, ValueError):
            issues.append("kwh must be a number")

        cost = None
        try:
            cost = Decimal(cost_raw)
            if cost < 0:
                issues.append("cost must not be negative")
        except (InvalidOperation, ValueError):
            issues.append("cost must be a number")

        if month is not None:
            key = month.isoformat()
            if key in seen_months:
                issues.append(f"duplicate month in file (also row {seen_months[key]})")
            else:
                seen_months[key] = row_number

        if issues:
            errors.append({"row": row_number, "message": "; ".join(issues)})
        else:
            parsed.append({"row": row_number, "month": month, "kwh": kwh, "cost": cost})

    return parsed, errors
