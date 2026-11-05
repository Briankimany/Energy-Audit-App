from server.extensions import db
from server.errors import BusinessError, NotFoundError
from server.models.institution import Institution
from server.repositories.building_repo import BuildingRepository
from server.repositories.institution_repo import InstitutionRepository


def _serialize(institution: Institution) -> dict:
    return {
        "id": institution.id,
        "name": institution.name,
        "currency": institution.currency,
        "max_buildings": institution.max_buildings,
        "created_at": institution.created_at.isoformat() if institution.created_at else None,
    }


def get_institution(user) -> dict:
    institution = InstitutionRepository().find_by_id(user.institution_id)
    if institution is None:
        raise NotFoundError("Institution not found")
    return _serialize(institution)


def update_institution(user, payload: dict) -> dict:
    repo = InstitutionRepository()
    institution = repo.find_by_id(user.institution_id)
    if institution is None:
        raise NotFoundError("Institution not found")

    if "name" in payload:
        existing = repo.find_by_name(payload["name"])
        if existing is not None and existing.id != institution.id:
            raise BusinessError(
                "Institution name already in use",
                {"name": ["already in use"]},
            )
        institution.name = payload["name"]

    if "currency" in payload:
        institution.currency = payload["currency"]

    if "max_buildings" in payload:
        current_count = BuildingRepository().count_for_institution(user.institution_id)
        if payload["max_buildings"] < current_count:
            raise BusinessError(
                "Building limit cannot be below the current building count",
                {"max_buildings": [f"current building count is {current_count}"]},
            )
        institution.max_buildings = payload["max_buildings"]

    db.session.commit()
    db.session.refresh(institution)
    return _serialize(institution)
