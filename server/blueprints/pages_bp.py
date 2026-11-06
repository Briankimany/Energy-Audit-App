from flask import Blueprint, redirect, render_template, request

from server.repositories.user_repo import UserRepository
from server.services.auth_service import decode_token

bp = Blueprint("pages", __name__)


def _current_user():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[len("Bearer "):].strip()
    payload = decode_token(token)
    return UserRepository().find_by_id(int(payload["sub"]))


@bp.get("/login")
def login():
    user = _current_user()
    if user is not None:
        return redirect("/dashboard")
    return render_template("login.html")


@bp.get("/register")
def register():
    user = _current_user()
    if user is not None:
        return redirect("/dashboard")
    return render_template("register.html")


@bp.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")
