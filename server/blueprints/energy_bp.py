from flask import Blueprint, g

from server.decorators import require_auth
from server.responses import success_response
from server.schemas import energy_schema
from server.services import energy_service

bp = Blueprint("energy", __name__, url_prefix="/api")


@bp.get("/buildings/<int:building_id>/energy")
@require_auth
def list_energy(building_id):
    return success_response(
        "Energy records fetched",
        energy_service.list_records(g.current_user, building_id),
    )


@bp.post("/buildings/<int:building_id>/energy")
@require_auth
def create_energy(building_id):
    payload = energy_schema.validate_create_payload()
    return success_response(
        "Energy record created",
        energy_service.create_record(g.current_user, building_id, payload),
        status_code=201,
    )


@bp.post("/buildings/<int:building_id>/energy/import")
@require_auth
def import_energy(building_id):
    payload = energy_schema.validate_import_payload()
    return success_response(
        "CSV processed",
        energy_service.import_csv(
            g.current_user,
            building_id,
            payload["csv"],
            payload["confirm"],
        ),
    )


@bp.patch("/buildings/<int:building_id>/energy/<int:record_id>")
@require_auth
def update_energy(building_id, record_id):
    payload = energy_schema.validate_update_payload()
    return success_response(
        "Energy record updated",
        energy_service.update_record(g.current_user, building_id, record_id, payload),
    )


@bp.delete("/buildings/<int:building_id>/energy/<int:record_id>")
@require_auth
def delete_energy(building_id, record_id):
    energy_service.delete_record(g.current_user, building_id, record_id)
    return success_response("Energy record deleted")
