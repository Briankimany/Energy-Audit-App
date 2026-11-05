from flask import Blueprint, g

from server.decorators import require_auth, require_role
from server.responses import success_response
from server.schemas import user_schema
from server.services import users_service

bp = Blueprint("users", __name__, url_prefix="/api")


@bp.get("/users")
@require_auth
@require_role("admin")
def list_users():
    return success_response("Users fetched", users_service.list_users(g.current_user))


@bp.post("/users")
@require_auth
@require_role("admin")
def create_user():
    payload = user_schema.validate_create_payload()
    return success_response(
        "User created",
        users_service.create_user(g.current_user, payload),
        status_code=201,
    )


@bp.patch("/users/<int:user_id>")
@require_auth
@require_role("admin")
def update_user(user_id):
    payload = user_schema.validate_update_payload()
    return success_response(
        "User updated",
        users_service.update_user(g.current_user, user_id, payload),
    )


@bp.delete("/users/<int:user_id>")
@require_auth
@require_role("admin")
def delete_user(user_id):
    users_service.delete_user(g.current_user, user_id)
    return success_response("User deleted")
