from flask import request

from server.errors import ValidationError


def get_json_object() -> dict:
    if not request.is_json:
        raise ValidationError(
            "Content-Type must be application/json",
            {"body": ["request body must be JSON"]},
        )
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError(
            "Request body must be a JSON object",
            {"body": ["request body must be a JSON object"]},
        )
    return payload


def require_fields(obj: dict, fields: list[str]) -> None:
    missing = [f for f in fields if f not in obj or obj[f] in (None, "")]
    if missing:
        raise ValidationError("Missing required fields", {"fields": missing})
