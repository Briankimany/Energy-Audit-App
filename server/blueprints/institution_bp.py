from flask import Blueprint, g

from server.decorators import require_auth, require_role
from server.responses import success_response
from server.schemas import institution_schema
from server.services import institution_service

bp = Blueprint("institution", __name__, url_prefix="/api")


@bp.get("/institution")
@require_auth
def get_institution():
    return success_response(
        "Institution fetched",
        institution_service.get_institution(g.current_user),
    )


@bp.patch("/institution")
@require_auth
@require_role("admin")
def update_institution():
    payload = institution_schema.validate_update_payload()
    return success_response(
        "Institution updated",
        institution_service.update_institution(g.current_user, payload),
    )
