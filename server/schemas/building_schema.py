from server.errors import ValidationError
from server.utils.validators import get_json_object, require_fields


def _validate_name(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("name must be a non-empty string", {"name": ["required"]})
    return value.strip()


def _validate_type(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("type must be a non-empty string", {"type": ["required"]})
    return value.strip()


def _validate_floor_area(value) -> float:
    try:
        area = float(value)
    except (TypeError, ValueError):
        raise ValidationError(
            "floor_area_m2 must be a number",
            {"floor_area_m2": ["must be a number"]},
        )
    if area <= 0:
        raise ValidationError(
            "floor_area_m2 must be positive",
            {"floor_area_m2": ["must be greater than 0"]},
        )
    return area


def _validate_operating_hours(value) -> int:
    try:
        hours = int(value)
    except (TypeError, ValueError):
        raise ValidationError(
            "operating_hours must be an integer",
            {"operating_hours": ["must be an integer"]},
        )
    if hours < 1 or hours > 24:
        raise ValidationError(
            "operating_hours must be between 1 and 24",
            {"operating_hours": ["must be 1..24"]},
        )
    return hours


def validate_create_payload() -> dict:
    payload = get_json_object()
    require_fields(payload, ["name", "type", "floor_area_m2", "operating_hours"])
    return {
        "name": _validate_name(payload["name"]),
        "type": _validate_type(payload["type"]),
        "floor_area_m2": _validate_floor_area(payload["floor_area_m2"]),
        "operating_hours": _validate_operating_hours(payload["operating_hours"]),
    }


def validate_update_payload() -> dict:
    payload = get_json_object()
    cleaned = {}
    if "name" in payload:
        cleaned["name"] = _validate_name(payload["name"])
    if "type" in payload:
        cleaned["type"] = _validate_type(payload["type"])
    if "floor_area_m2" in payload:
        cleaned["floor_area_m2"] = _validate_floor_area(payload["floor_area_m2"])
    if "operating_hours" in payload:
        cleaned["operating_hours"] = _validate_operating_hours(payload["operating_hours"])
    return cleaned
