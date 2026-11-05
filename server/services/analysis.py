from collections import defaultdict

ANOMALY_THRESHOLD = 0.30


def _record_value(record, key: str) -> float:
    value = getattr(record, key, None)
    if value is None:
        value = record[key]
    return float(value)


def _record_month(record) -> str:
    month = getattr(record, "month", None)
    if month is None:
        month = record["month"]
    if hasattr(month, "strftime"):
        return month.strftime("%Y-%m")
    return str(month)[:7]


def annual_kwh(records: list) -> float:
    return round(sum(_record_value(record, "kwh") for record in records), 2)


def annual_cost(records: list) -> float:
    return round(sum(_record_value(record, "cost") for record in records), 2)


def monthly_series(records: list) -> list[dict]:
    return [
        {
            "month": _record_month(record),
            "kwh": _record_value(record, "kwh"),
            "cost": _record_value(record, "cost"),
        }
        for record in records
    ]


def eui(total_kwh: float, floor_area_m2: float) -> float | None:
    if not floor_area_m2 or float(floor_area_m2) <= 0:
        return None
    return round(float(total_kwh) / float(floor_area_m2), 2)


def eui_note(month_count: int) -> str:
    if month_count >= 12:
        return "complete"
    if month_count >= 6:
        return "partial"
    return "insufficient"


def _average_of_others(records: list, excluded_index: int) -> float | None:
    remaining = [
        _record_value(record, "kwh") for i, record in enumerate(records) if i != excluded_index
    ]
    if not remaining:
        return None
    return round(sum(remaining) / len(remaining), 2)


def anomaly_months(records: list, threshold: float = ANOMALY_THRESHOLD) -> list:
    anomalies = []
    for index, record in enumerate(records):
        average = _average_of_others(records, index)
        if average is None:
            continue
        value = _record_value(record, "kwh")
        if value > average * (1 + threshold):
            anomalies.append(
                {
                    "month": _record_month(record),
                    "kwh": value,
                    "average_other_months": average,
                    "percent_above": round((value - average) / average * 100, 2),
                }
            )
    return anomalies


def compare_buildings(analyses: list, building_types: dict) -> tuple:
    result = []
    for analysis in analyses:
        result.append(
            {
                "id": analysis["building_id"],
                "name": analysis["name"],
                "type": analysis["type"],
                "floor_area_m2": analysis["floor_area_m2"],
                "total_kwh": analysis["total_kwh"],
                "total_cost": analysis["total_cost"],
                "eui": analysis["eui"],
                "eui_note": analysis["eui_note"],
            }
        )
    types = set(building_types.values())
    warning = (
        "Comparison may not be fair because building types differ between buildings."
        if len(types) > 1
        else None
    )
    return result, warning


def aggregation_by_month(groups: list) -> list:
    grouped = defaultdict(lambda: {"kwh": 0.0, "cost": 0.0})
    for group in groups:
        for record in group:
            key = _record_month(record)
            grouped[key]["kwh"] += _record_value(record, "kwh")
            grouped[key]["cost"] += _record_value(record, "cost")
    ordered = sorted(grouped.items(), key=lambda item: item[0])
    return [
        {
            "month": key,
            "kwh": round(total["kwh"], 2),
            "cost": round(total["cost"], 2),
        }
        for key, total in ordered
    ]
