from server.extensions import db
from server.models.user import User


class UserRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def find_by_email(self, email: str):
        return self.session.query(User).filter_by(email=email).first()

    def find_by_id(self, user_id: int):
        return self.session.get(User, user_id)

    def list_for_institution(self, institution_id: int):
        return self.session.query(User).filter(User.institution_id == institution_id).all()
