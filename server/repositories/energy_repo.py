from server.extensions import db
from server.models.energy_record import EnergyRecord


class EnergyRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def list_for_building(self, institution_id: int, building_id: int):
        return (
            self.session.query(EnergyRecord)
            .filter(
                EnergyRecord.institution_id == institution_id,
                EnergyRecord.building_id == building_id,
            )
            .order_by(EnergyRecord.month)
            .all()
        )

    def find_by_id_for_building(self, record_id: int, building_id: int):
        return (
            self.session.query(EnergyRecord)
            .filter(
                EnergyRecord.id == record_id,
                EnergyRecord.building_id == building_id,
            )
            .first()
        )

    def find_by_building_and_month(self, building_id: int, month):
        return (
            self.session.query(EnergyRecord)
            .filter(
                EnergyRecord.building_id == building_id,
                EnergyRecord.month == month,
            )
            .first()
        )

    def create(self, **kwargs):
        record = EnergyRecord(**kwargs)
        self.session.add(record)
        return record
