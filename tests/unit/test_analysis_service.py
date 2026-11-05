from server.services import analysis as analysis_service


def _record(month: str, kwh, cost: float = 10.0) -> dict:
    return {"month": month, "kwh": kwh, "cost": cost}


def test_annual_kwh_sums_records():
    records = [_record("2025-01", 100.0), _record("2025-02", 200.5)]
    assert analysis_service.annual_kwh(records) == 300.5


def test_annual_cost_sums_records():
    records = [_record("2025-01", 100.0, 10.0), _record("2025-02", 200.5, 20.0)]
    assert analysis_service.annual_cost(records) == 30.0


def test_eui_computes_ratio():
    assert analysis_service.eui(1200.0, 300.0) == 4.0


def test_eui_note_months():
    assert analysis_service.eui_note(12) == "complete"
    assert analysis_service.eui_note(6) == "partial"
    assert analysis_service.eui_note(2) == "insufficient"


def test_anomaly_none_when_within_threshold():
    records = [
        _record("2025-01", 100.0),
        _record("2025-02", 100.0),
        _record("2025-03", 130.0),
    ]
    assert analysis_service.anomaly_months(records, threshold=0.30) == []


def test_anomaly_flags_above_threshold():
    records = [
        _record("2025-01", 100.0),
        _record("2025-02", 150.0),
    ]
    anomalies = analysis_service.anomaly_months(records, threshold=0.30)
    assert len(anomalies) == 1
    assert anomalies[0]["month"] == "2025-02"
    assert anomalies[0]["percent_above"] == 50.0


def test_anomaly_skips_single_record():
    assert analysis_service.anomaly_months([_record("2025-01", 500.0)]) == []


def test_compare_warning_when_types_differ():
    analyses = [
        {"building_id": 1, "name": "A", "type": "office", "floor_area_m2": 100.0, "total_kwh": 100.0, "total_cost": 1.0, "eui": 1.0, "eui_note": "complete"},
        {"building_id": 2, "name": "B", "type": "lab", "floor_area_m2": 100.0, "total_kwh": 100.0, "total_cost": 1.0, "eui": 1.0, "eui_note": "complete"},
    ]
    types = {a["building_id"]: a["type"] for a in analyses}
    comparisons, warning = analysis_service.compare_buildings(analyses, types)
    assert len(comparisons) == 2
    assert warning is not None
    assert "fair" in warning


def test_compare_no_warning_when_same_type():
    analyses = [
        {"building_id": 1, "name": "A", "type": "office", "floor_area_m2": 100.0, "total_kwh": 100.0, "total_cost": 1.0, "eui": 1.0, "eui_note": "complete"},
        {"building_id": 2, "name": "B", "type": "office", "floor_area_m2": 200.0, "total_kwh": 200.0, "total_cost": 2.0, "eui": 1.0, "eui_note": "complete"},
    ]
    types = {a["building_id"]: a["type"] for a in analyses}
    comparisons, warning = analysis_service.compare_buildings(analyses, types)
    assert len(comparisons) == 2
    assert warning is None


def test_aggregation_by_month_sums_groups():
    series = [
        [_record("2025-01", 10.0), _record("2025-02", 20.0)],
        [_record("2025-01", 5.0), _record("2025-02", 5.0)],
    ]
    result = analysis_service.aggregation_by_month(series)
    assert len(result) == 2
    assert result[0]["kwh"] == 15.0
    assert result[0]["cost"] == 20.0
    assert result[1]["kwh"] == 25.0
