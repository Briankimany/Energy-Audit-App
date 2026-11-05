from server.errors import ValidationError
from server.utils.validators import get_json_object, require_fields

PASSWORD_MIN_LENGTH = 8


def _require_password_length(password: str, field: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(
            f"{field} must be at least {PASSWORD_MIN_LENGTH} characters",
            {field: [f"min length is {PASSWORD_MIN_LENGTH}"]},
        )


def validate_register_payload() -> dict:
    payload = get_json_object()
    require_fields(payload, ["institution_name", "admin_name", "admin_email", "password"])
    _require_password_length(payload["password"], "password")
    return payload


def validate_login_payload() -> dict:
    payload = get_json_object()
    require_fields(payload, ["email", "password"])
    return payload


def validate_change_password_payload() -> dict:
    payload = get_json_object()
    require_fields(payload, ["current_password", "new_password"])
    _require_password_length(payload["new_password"], "new_password")
    return payload
