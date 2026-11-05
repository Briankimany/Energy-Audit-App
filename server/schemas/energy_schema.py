from decimal import Decimal, InvalidOperation

from server.errors import ValidationError
from server.utils.dates import parse_month
from server.utils.validators import get_json_object, require_fields


def _validate_month(value):
    try:
        return parse_month(value)
    except ValueError as exc:
        raise ValidationError(str(exc), {"month": ["must be YYYY-MM"]}) from exc


def _validate_non_negative(value, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValidationError(f"{field} must be a number", {field: ["must be a number"]})
    if number < 0:
        raise ValidationError(
            f"{field} must not be negative",
            {field: ["must be greater than or equal to 0"]},
        )
    return number


def validate_create_payload() -> dict:
    payload = get_json_object()
    require_fields(payload, ["month", "kwh", "cost"])
    return {
        "month": _validate_month(payload["month"]),
        "kwh": _validate_non_negative(payload["kwh"], "kwh"),
        "cost": _validate_non_negative(payload["cost"], "cost"),
    }


def validate_update_payload() -> dict:
    payload = get_json_object()
    cleaned = {}
    if "month" in payload:
        cleaned["month"] = _validate_month(payload["month"])
    if "kwh" in payload:
        cleaned["kwh"] = _validate_non_negative(payload["kwh"], "kwh")
    if "cost" in payload:
        cleaned["cost"] = _validate_non_negative(payload["cost"], "cost")
    return cleaned


def validate_import_payload() -> dict:
    payload = get_json_object()
    require_fields(payload, ["csv"])

    csv_text = payload["csv"]
    if not isinstance(csv_text, str):
        raise ValidationError("csv must be a string", {"csv": ["must be a string"]})

    confirm = payload.get("confirm", False)
    if not isinstance(confirm, bool):
        raise ValidationError("confirm must be a boolean", {"confirm": ["must be a boolean"]})

    return {"csv": csv_text, "confirm": confirm}
