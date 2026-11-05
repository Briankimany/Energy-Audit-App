from server.extensions import db
from server.errors import BusinessError, NotFoundError
from server.models.user import User
from server.repositories.user_repo import UserRepository
from server.utils.security import hash_password


def _serialize(user: User) -> dict:
    return {
        "id": user.id,
        "institution_id": user.institution_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "must_change_password": user.must_change_password,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def list_users(user) -> list[dict]:
    users = UserRepository().list_for_institution(user.institution_id)
    return [_serialize(item) for item in users]


def create_user(user, payload: dict) -> dict:
    repo = UserRepository()
    if repo.find_by_email(payload["email"]) is not None:
        raise BusinessError("Email already registered", {"email": ["already in use"]})

    new_user = repo.create(
        institution_id=user.institution_id,
        name=payload["name"],
        email=payload["email"],
        password_hash=hash_password(payload["password"]),
        role="auditor",
        must_change_password=True,
    )
    db.session.commit()
    db.session.refresh(new_user)
    return _serialize(new_user)


def update_user(user, user_id: int, payload: dict) -> dict:
    repo = UserRepository()
    target = repo.find_by_id_for_institution(user_id, user.institution_id)
    if target is None:
        raise NotFoundError("User not found")

    if "name" in payload:
        target.name = payload["name"]
    if "password" in payload:
        target.password_hash = hash_password(payload["password"])
        target.must_change_password = True

    db.session.commit()
    db.session.refresh(target)
    return _serialize(target)


def delete_user(user, user_id: int) -> None:
    if user_id == user.id:
        raise BusinessError("You cannot delete your own account")

    repo = UserRepository()
    target = repo.find_by_id_for_institution(user_id, user.institution_id)
    if target is None:
        raise NotFoundError("User not found")

    db.session.delete(target)
    db.session.commit()
