from server.extensions import db
from server.models.user import User


class UserRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def find_by_email(self, email: str):
        return self.session.query(User).filter_by(email=email).first()

    def find_by_id(self, user_id: int):
        return self.session.get(User, user_id)

    def find_by_id_for_institution(self, user_id: int, institution_id: int):
        return (
            self.session.query(User)
            .filter(User.id == user_id, User.institution_id == institution_id)
            .first()
        )

    def list_for_institution(self, institution_id: int):
        return (
            self.session.query(User)
            .filter(User.institution_id == institution_id)
            .order_by(User.name)
            .all()
        )

    def create(self, **kwargs):
        user = User(**kwargs)
        self.session.add(user)
        return user
