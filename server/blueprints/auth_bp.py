from flask import Blueprint, g

from server.decorators import require_auth
from server.responses import success_response
from server.schemas import auth_schema
from server.services import auth_service

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register-institution")
def register_institution():
    payload = auth_schema.validate_register_payload()
    result = auth_service.register_institution(payload)
    return success_response("Institution created", result, status_code=201)


@bp.post("/login")
def login():
    payload = auth_schema.validate_login_payload()
    result = auth_service.login(payload)
    return success_response("Authenticated", result)


@bp.post("/logout")
@require_auth
def logout():
    auth_service.logout(g.current_user)
    return success_response("Logged out")


@bp.post("/change-password")
@require_auth
def change_password():
    payload = auth_schema.validate_change_password_payload()
    auth_service.change_password(g.current_user.id, payload)
    return success_response("Password changed")
