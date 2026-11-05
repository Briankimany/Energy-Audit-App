import datetime

import jwt
from flask import current_app

from server.extensions import db
from server.errors import BusinessError, NotFoundError, UnauthorizedError
from server.models.institution import Institution
from server.models.user import User
from server.repositories.user_repo import UserRepository
from server.utils.security import hash_password, verify_password


def create_token(user: User) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user.id),
        "institution_id": str(user.institution_id),
        "role": user.role,
        "iat": now,
        "exp": now + datetime.timedelta(seconds=current_app.config["JWT_EXPIRATION_SECONDS"]),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid token") from exc


def register_institution(payload: dict) -> dict:
    institution_name = payload["institution_name"].strip()
    admin_name = payload["admin_name"].strip()
    admin_email = payload["admin_email"].strip().lower()
    password = payload["password"]

    if UserRepository().find_by_email(admin_email) is not None:
        raise BusinessError("Email already registered", {"email": ["already in use"]})

    institution = Institution(name=institution_name)
    admin = User(
        institution=institution,
        name=admin_name,
        email=admin_email,
        password_hash=hash_password(password),
        role="admin",
        must_change_password=True,
    )
    db.session.add(institution)
    db.session.add(admin)
    db.session.commit()
    db.session.refresh(institution)
    db.session.refresh(admin)

    return {
        "institution_id": institution.id,
        "user_id": admin.id,
        "access_token": create_token(admin),
        "token_type": "Bearer",
    }


def login(payload: dict) -> dict:
    email = payload["email"].strip().lower()
    password = payload["password"]

    user = UserRepository().find_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    return {
        "access_token": create_token(user),
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "institution_id": user.institution_id,
            "role": user.role,
            "must_change_password": user.must_change_password,
        },
    }


def logout(user: User) -> None:
    return None


def change_password(user_id: int, payload: dict) -> None:
    user = UserRepository().find_by_id(user_id)
    if user is None:
        raise NotFoundError("User not found")

    if not verify_password(payload["current_password"], user.password_hash):
        raise UnauthorizedError("Current password is incorrect")

    user.password_hash = hash_password(payload["new_password"])
    user.must_change_password = False
    db.session.commit()
