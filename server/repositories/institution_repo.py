from server.extensions import db
from server.models.institution import Institution


class InstitutionRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def find_by_id(self, institution_id: int):
        return self.session.get(Institution, institution_id)

    def find_by_name(self, name: str):
        return self.session.query(Institution).filter_by(name=name).first()
