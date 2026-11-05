from server.extensions import db
from server.models.building import Building


class BuildingRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def list_for_institution(self, institution_id: int):
        return (
            self.session.query(Building)
            .filter(Building.institution_id == institution_id)
            .order_by(Building.name)
            .all()
        )

    def find_by_id_for_institution(self, building_id: int, institution_id: int):
        return (
            self.session.query(Building)
            .filter(Building.id == building_id, Building.institution_id == institution_id)
            .first()
        )

    def find_by_name(self, institution_id: int, name: str):
        return (
            self.session.query(Building)
            .filter(Building.institution_id == institution_id, Building.name == name)
            .first()
        )

    def count_for_institution(self, institution_id: int) -> int:
        return (
            self.session.query(Building)
            .filter(Building.institution_id == institution_id)
            .count()
        )

    def create(self, **kwargs):
        building = Building(**kwargs)
        self.session.add(building)
        return building
