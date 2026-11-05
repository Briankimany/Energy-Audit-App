from server.errors import ValidationError
from server.utils.validators import get_json_object


def _validate_name(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("name must be a non-empty string", {"name": ["required"]})
    return value.strip()


def _validate_currency(value) -> str:
    currency = value.strip() if isinstance(value, str) else ""
    if len(currency) != 3 or not currency.isalpha():
        raise ValidationError(
            "currency must be a 3-letter code",
            {"currency": ["must be a 3-letter code"]},
        )
    return currency.upper()


def _validate_max_buildings(value) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        raise ValidationError(
            "max_buildings must be an integer",
            {"max_buildings": ["must be an integer"]},
        )
    if limit < 1 or limit > 50:
        raise ValidationError(
            "max_buildings must be between 1 and 50",
            {"max_buildings": ["must be 1..50"]},
        )
    return limit


def validate_update_payload() -> dict:
    payload = get_json_object()
    cleaned = {}
    if "name" in payload:
        cleaned["name"] = _validate_name(payload["name"])
    if "currency" in payload:
        cleaned["currency"] = _validate_currency(payload["currency"])
    if "max_buildings" in payload:
        cleaned["max_buildings"] = _validate_max_buildings(payload["max_buildings"])
    return cleaned
