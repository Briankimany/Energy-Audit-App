from flask import Blueprint, g

from server.decorators import require_auth
from server.responses import success_response
from server.services import dashboard_service

bp = Blueprint("analysis", __name__, url_prefix="/api")


@bp.get("/buildings/<int:building_id>/analysis")
@require_auth
def building_analysis(building_id):
    return success_response(
        "Analysis computed",
        dashboard_service.analyze_building(g.current_user, building_id),
    )


@bp.get("/analysis/compare")
@require_auth
def compare():
    comparisons, warning = dashboard_service.build_compare(g.current_user)
    return success_response(
        "Building comparison",
        {"comparisons": comparisons, "warning": warning},
    )


@bp.get("/dashboard")
@require_auth
def dashboard():
    return success_response(
        "Dashboard summary",
        dashboard_service.dashboard_summary(g.current_user),
    )
