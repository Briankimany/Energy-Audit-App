from collections import defaultdict

from server.errors import NotFoundError
from server.repositories.building_repo import BuildingRepository
from server.repositories.energy_repo import EnergyRepository
from server.services import analysis


def _building_analysis(building, records):
    return {
        "building_id": building.id,
        "name": building.name,
        "type": building.type,
        "floor_area_m2": float(building.floor_area_m2),
        "total_kwh": analysis.annual_kwh(records),
        "total_cost": analysis.annual_cost(records),
        "monthly_records": analysis.monthly_series(records),
        "eui": analysis.eui(analysis.annual_kwh(records), building.floor_area_m2),
        "eui_note": analysis.eui_note(len(records)),
        "anomalies": analysis.anomaly_months(records),
    }


def analyze_building(user, building_id: int):
    building = BuildingRepository().find_by_id_for_institution(
        building_id, user.institution_id
    )
    if building is None:
        raise NotFoundError("Building not found")
    records = EnergyRepository().list_for_building(user.institution_id, building_id)
    return _building_analysis(building, records)


def build_compare(user) -> tuple[list[dict], str | None]:
    buildings = BuildingRepository().list_for_institution(user.institution_id)
    analyses = [analyze_building(user, building.id) for building in buildings]
    types = {analysis["building_id"]: analysis["type"] for analysis in analyses}
    return analysis.compare_buildings(analyses, types)


def dashboard_summary(user) -> dict:
    buildings = BuildingRepository().list_for_institution(user.institution_id)
    grouped = defaultdict(list)
    total_kwh = 0.0
    total_cost = 0.0
    comparisons = []
    warning = None
    types = set()
    anomalies = []

    for building in buildings:
        records = EnergyRepository().list_for_building(user.institution_id, building.id)
        building_kwh = analysis.annual_kwh(records)
        building_cost = analysis.annual_cost(records)
        total_kwh += building_kwh
        total_cost += building_cost

        for record in records:
            grouped[record.month].append(record)

        building_analysis = _building_analysis(building, records)
        if building_analysis["eui"] is None:
            continue
        comparisons.append(building_analysis)
        types.add(building.type)
        if len(types) > 1 and warning is None:
            warning = (
                "Comparison may not be fair because building types differ between buildings."
            )

        for anomaly in analysis.anomaly_months(records):
            anomalies.append(
                {
                    "building_id": building.id,
                    "month": anomaly["month"],
                    "percent_above": anomaly["percent_above"],
                }
            )

    return {
        "institution_id": user.institution_id,
        "building_count": len(buildings),
        "total_kwh": round(total_kwh, 2),
        "total_cost": round(total_cost, 2),
        "monthly_series": analysis.aggregation_by_month([grouped[month] for month in grouped]),
        "comparisons": comparisons,
        "warning": warning,
        "anomalies": anomalies,
    }
