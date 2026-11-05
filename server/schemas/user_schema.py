from server.errors import ValidationError
from server.utils.validators import get_json_object, require_fields

PASSWORD_MIN_LENGTH = 8


def _validate_name(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("name must be a non-empty string", {"name": ["required"]})
    return value.strip()


def _validate_email(value) -> str:
    email = value.strip().lower() if isinstance(value, str) else ""
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValidationError("email must be valid", {"email": ["invalid email"]})
    return email


def _validate_password(value) -> str:
    if not isinstance(value, str) or len(value) < PASSWORD_MIN_LENGTH:
        raise ValidationError(
            f"password must be at least {PASSWORD_MIN_LENGTH} characters",
            {"password": [f"min length is {PASSWORD_MIN_LENGTH}"]},
        )
    return value


def validate_create_payload() -> dict:
    payload = get_json_object()
    require_fields(payload, ["name", "email", "password"])
    return {
        "name": _validate_name(payload["name"]),
        "email": _validate_email(payload["email"]),
        "password": _validate_password(payload["password"]),
    }


def validate_update_payload() -> dict:
    payload = get_json_object()
    cleaned = {}
    if "name" in payload:
        cleaned["name"] = _validate_name(payload["name"])
    if "password" in payload:
        cleaned["password"] = _validate_password(payload["password"])
    return cleaned
