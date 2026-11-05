import functools

from flask import g, request

from server.errors import ForbiddenError, UnauthorizedError
from server.repositories.user_repo import UserRepository
from server.services.auth_service import decode_token


def require_auth(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise UnauthorizedError("Missing bearer token")

        token = header[len("Bearer "):].strip()
        payload = decode_token(token)

        user = UserRepository().find_by_id(int(payload["sub"]))
        if user is None:
            raise UnauthorizedError("Invalid token")

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def require_role(*roles):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if user is None or user.role not in roles:
                raise ForbiddenError("Forbidden")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
