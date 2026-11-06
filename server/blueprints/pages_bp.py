from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)


@bp.get("/login")
def login():
    return render_template("login.html")


@bp.get("/register")
def register():
    return render_template("register.html")


@bp.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@bp.get("/buildings")
def buildings():
    return render_template("buildings.html")


@bp.get("/buildings/<int:building_id>/energy")
def energy(building_id: int):
    return render_template("energy_records.html", building_id=building_id)


@bp.get("/users")
def users():
    return render_template("users.html")


@bp.get("/settings")
def settings():
    return render_template("settings.html")


@bp.get("/analysis/compare")
def compare():
    return render_template("compare.html")
