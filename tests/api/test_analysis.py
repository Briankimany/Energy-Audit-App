BUILDING = {
    "name": "Main Block",
    "type": "office",
    "floor_area_m2": 250,
    "operating_hours": 9,
}

OTHER_INSTITUTION = {
    "institution_name": "Other Institute",
    "admin_name": "Other Admin",
    "admin_email": "other@test.org",
    "password": "password123",
}


def _create_building(client, headers, name="Main Block", building_type="office"):
    response = client.post(
        "/api/buildings",
        headers=headers,
        json=dict(BUILDING, name=name, type=building_type),
    )
    return response.get_json()["data"]


def _add(client, headers, building_id, month, kwh, cost):
    return client.post(
        f"/api/buildings/{building_id}/energy",
        headers=headers,
        json={"month": month, "kwh": kwh, "cost": cost},
    )


def _other_headers(client):
    client.post("/api/auth/register-institution", json=OTHER_INSTITUTION)
    token = client.post(
        "/api/auth/login",
        json={"email": "other@test.org", "password": "password123"},
    ).get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_twelve_months(client, headers, building_id, high_month=None):
    high_kwh = 1000.0
    expected_total = 0.0
    for month_number in range(1, 13):
        month = f"2025-{month_number:02d}"
        kwh = high_kwh if month == high_month else 100.0
        cost = 200.0
        response = _add(client, headers, building_id, month, kwh, cost)
        assert response.status_code == 201
        expected_total += kwh


def test_building_analysis_returns_annual_totals_and_eui(client, admin_headers):
    building = _create_building(client, admin_headers)
    _seed_twelve_months(client, admin_headers, building["id"], high_month="2025-06")

    response = client.get(
        f"/api/buildings/{building['id']}/analysis", headers=admin_headers
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["building_id"] == building["id"]
    assert data["total_kwh"] == 2100.0
    assert data["total_cost"] == 2400.0
    assert data["eui"] == 8.4
    assert data["eui_note"] == "complete"
    assert len(data["monthly_records"]) == 12


def test_building_analysis_flags_anomaly(client, admin_headers):
    building = _create_building(client, admin_headers)
    _seed_twelve_months(client, admin_headers, building["id"], high_month="2025-06")

    response = client.get(
        f"/api/buildings/{building['id']}/analysis", headers=admin_headers
    )
    data = response.get_json()["data"]
    assert response.status_code == 200
    assert len(data["monthly_records"]) == 12
    assert len(data["anomalies"]) == 1
    assert data["anomalies"][0]["month"] == "2025-06"


def test_comparison_same_type_has_no_warning(client, admin_headers):
    _create_building(client, admin_headers, name="Compare A")
    _create_building(client, admin_headers, name="Compare B", building_type="office")

    response = client.get("/api/analysis/compare", headers=admin_headers)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data["comparisons"]) == 2
    assert data["warning"] is None


def test_comparison_warns_when_types_differ(client, admin_headers):
    _create_building(client, admin_headers, name="Compare Lab", building_type="lab")
    _create_building(client, admin_headers, name="Compare Office", building_type="office")

    response = client.get("/api/analysis/compare", headers=admin_headers)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data["comparisons"]) == 2
    assert data["warning"] is not None


def test_dashboard_summary(client, admin_headers):
    building = _create_building(client, admin_headers)
    _add(client, admin_headers, building["id"], "2025-01", 100.0, 200.0)
    _add(client, admin_headers, building["id"], "2025-02", 150.0, 300.0)

    response = client.get("/api/dashboard", headers=admin_headers)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["building_count"] == 1
    assert data["total_kwh"] == 250.0
    assert data["total_cost"] == 500.0
    assert len(data["monthly_series"]) == 2


def test_cross_tenant_analysis_is_404(client, admin_headers):
    building = _create_building(client, admin_headers)
    _seed_twelve_months(client, admin_headers, building["id"])
    other = _other_headers(client)

    response = client.get(
        f"/api/buildings/{building['id']}/analysis", headers=other
    )
    assert response.status_code == 404
