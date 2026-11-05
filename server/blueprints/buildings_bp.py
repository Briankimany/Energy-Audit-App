from flask import Blueprint, g

from server.decorators import require_auth
from server.responses import success_response
from server.schemas import building_schema
from server.services import buildings_service

bp = Blueprint("buildings", __name__, url_prefix="/api")


@bp.get("/buildings")
@require_auth
def list_buildings():
    return success_response("Buildings fetched", buildings_service.list_buildings(g.current_user))


@bp.post("/buildings")
@require_auth
def create_building():
    payload = building_schema.validate_create_payload()
    return success_response(
        "Building created",
        buildings_service.create_building(g.current_user, payload),
        status_code=201,
    )


@bp.get("/buildings/<int:building_id>")
@require_auth
def get_building(building_id):
    return success_response(
        "Building fetched",
        buildings_service.get_building(g.current_user, building_id),
    )


@bp.patch("/buildings/<int:building_id>")
@require_auth
def update_building(building_id):
    payload = building_schema.validate_update_payload()
    return success_response(
        "Building updated",
        buildings_service.update_building(g.current_user, building_id, payload),
    )


@bp.delete("/buildings/<int:building_id>")
@require_auth
def delete_building(building_id):
    buildings_service.delete_building(g.current_user, building_id)
    return success_response("Building deleted")
