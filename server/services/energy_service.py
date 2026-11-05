from server.extensions import db
from server.errors import BusinessError, NotFoundError
from server.models.energy_record import EnergyRecord
from server.repositories.building_repo import BuildingRepository
from server.repositories.energy_repo import EnergyRepository
from server.utils.csv import parse_energy_csv
from server.utils.dates import month_key


def _serialize(record: EnergyRecord) -> dict:
    return {
        "id": record.id,
        "institution_id": record.institution_id,
        "building_id": record.building_id,
        "month": month_key(record.month),
        "kwh": float(record.kwh),
        "cost": float(record.cost),
    }


def _get_building(user, building_id: int):
    building = BuildingRepository().find_by_id_for_institution(
        building_id, user.institution_id
    )
    if building is None:
        raise NotFoundError("Building not found")
    return building


def list_records(user, building_id: int) -> list[dict]:
    _get_building(user, building_id)
    records = EnergyRepository().list_for_building(user.institution_id, building_id)
    return [_serialize(record) for record in records]


def create_record(user, building_id: int, payload: dict) -> dict:
    _get_building(user, building_id)
    repo = EnergyRepository()

    if repo.find_by_building_and_month(building_id, payload["month"]) is not None:
        raise BusinessError(
            "A record for that month already exists",
            {"month": ["already recorded for this building"]},
        )

    record = repo.create(
        institution_id=user.institution_id,
        building_id=building_id,
        month=payload["month"],
        kwh=payload["kwh"],
        cost=payload["cost"],
    )
    db.session.commit()
    db.session.refresh(record)
    return _serialize(record)


def update_record(user, building_id: int, record_id: int, payload: dict) -> dict:
    _get_building(user, building_id)
    repo = EnergyRepository()

    record = repo.find_by_id_for_building(record_id, building_id)
    if record is None:
        raise NotFoundError("Energy record not found")

    if "month" in payload and payload["month"] != record.month:
        existing = repo.find_by_building_and_month(building_id, payload["month"])
        if existing is not None and existing.id != record.id:
            raise BusinessError(
                "A record for that month already exists",
                {"month": ["already recorded for this building"]},
            )
        record.month = payload["month"]

    if "kwh" in payload:
        record.kwh = payload["kwh"]
    if "cost" in payload:
        record.cost = payload["cost"]

    db.session.commit()
    db.session.refresh(record)
    return _serialize(record)


def delete_record(user, building_id: int, record_id: int) -> None:
    _get_building(user, building_id)
    repo = EnergyRepository()

    record = repo.find_by_id_for_building(record_id, building_id)
    if record is None:
        raise NotFoundError("Energy record not found")

    db.session.delete(record)
    db.session.commit()


def import_csv(user, building_id: int, csv_text: str, confirm: bool) -> dict:
    _get_building(user, building_id)
    repo = EnergyRepository()
    parsed_rows, errors = parse_energy_csv(csv_text)

    valid_rows = []
    for row in parsed_rows:
        if repo.find_by_building_and_month(building_id, row["month"]) is not None:
            errors.append({"row": row["row"], "message": "month already recorded for this building"})
        else:
            valid_rows.append(row)

    errors.sort(key=lambda item: item["row"])
    result = {
        "valid_rows": len(valid_rows),
        "errors": errors,
        "imported": 0,
    }

    if not confirm:
        result["requires_confirmation"] = True
        return result

    for row in valid_rows:
        repo.create(
            institution_id=user.institution_id,
            building_id=building_id,
            month=row["month"],
            kwh=row["kwh"],
            cost=row["cost"],
        )
    db.session.commit()
    result["imported"] = len(valid_rows)
    return result
