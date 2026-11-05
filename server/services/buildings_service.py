from decimal import Decimal

from server.extensions import db
from server.errors import BusinessError, NotFoundError
from server.models.building import Building
from server.repositories.building_repo import BuildingRepository
from server.repositories.institution_repo import InstitutionRepository


def _serialize(building: Building) -> dict:
    return {
        "id": building.id,
        "institution_id": building.institution_id,
        "name": building.name,
        "type": building.type,
        "floor_area_m2": float(building.floor_area_m2),
        "operating_hours": building.operating_hours,
    }


def list_buildings(user) -> list[dict]:
    buildings = BuildingRepository().list_for_institution(user.institution_id)
    return [_serialize(item) for item in buildings]


def create_building(user, payload: dict) -> dict:
    institution = InstitutionRepository().find_by_id(user.institution_id)
    if institution is None:
        raise NotFoundError("Institution not found")

    repo = BuildingRepository()
    if repo.count_for_institution(user.institution_id) >= institution.max_buildings:
        raise BusinessError(
            "Building limit reached",
            {"buildings": [f"the limit is {institution.max_buildings}"]},
        )

    if repo.find_by_name(user.institution_id, payload["name"]) is not None:
        raise BusinessError("Building name already in use", {"name": ["already in use"]})

    building = repo.create(
        institution_id=user.institution_id,
        name=payload["name"],
        type=payload["type"],
        floor_area_m2=Decimal(str(payload["floor_area_m2"])),
        operating_hours=payload["operating_hours"],
    )
    db.session.commit()
    db.session.refresh(building)
    return _serialize(building)


def get_building(user, building_id: int) -> dict:
    building = BuildingRepository().find_by_id_for_institution(
        building_id, user.institution_id
    )
    if building is None:
        raise NotFoundError("Building not found")
    return _serialize(building)


def update_building(user, building_id: int, payload: dict) -> dict:
    repo = BuildingRepository()
    building = repo.find_by_id_for_institution(building_id, user.institution_id)
    if building is None:
        raise NotFoundError("Building not found")

    if "name" in payload:
        existing = repo.find_by_name(user.institution_id, payload["name"])
        if existing is not None and existing.id != building.id:
            raise BusinessError("Building name already in use", {"name": ["already in use"]})
        building.name = payload["name"]
    if "type" in payload:
        building.type = payload["type"]
    if "floor_area_m2" in payload:
        building.floor_area_m2 = Decimal(str(payload["floor_area_m2"]))
    if "operating_hours" in payload:
        building.operating_hours = payload["operating_hours"]

    db.session.commit()
    db.session.refresh(building)
    return _serialize(building)


def delete_building(user, building_id: int) -> None:
    repo = BuildingRepository()
    building = repo.find_by_id_for_institution(building_id, user.institution_id)
    if building is None:
        raise NotFoundError("Building not found")

    db.session.delete(building)
    db.session.commit()
