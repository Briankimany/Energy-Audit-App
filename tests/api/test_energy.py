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

CSV_OK = "month,kwh,cost\n2025-01,1000,2000\n2025-02,1100,2200\n"


def _create_building(client, headers, name="Main Block"):
    payload = dict(BUILDING, name=name)
    response = client.post("/api/buildings", headers=headers, json=payload)
    return response.get_json()["data"]


def _other_headers(client):
    client.post("/api/auth/register-institution", json=OTHER_INSTITUTION)
    token = client.post(
        "/api/auth/login",
        json={"email": "other@test.org", "password": "password123"},
    ).get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _add(client, headers, building_id, month="2025-01", kwh=1000, cost=2000):
    return client.post(
        f"/api/buildings/{building_id}/energy",
        headers=headers,
        json={"month": month, "kwh": kwh, "cost": cost},
    )


def test_create_and_list_energy(client, admin_headers):
    building = _create_building(client, admin_headers)

    response = _add(client, admin_headers, building["id"], month="2025-01", kwh=1200.5, cost=2400)
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["month"] == "2025-01"
    assert data["kwh"] == 1200.5
    assert data["cost"] == 2400.0
    assert data["building_id"] == building["id"]

    listing = client.get(
        f"/api/buildings/{building['id']}/energy", headers=admin_headers
    ).get_json()["data"]
    assert len(listing) == 1
    assert listing[0]["id"] == data["id"]


def test_energy_requires_auth(client, admin_headers):
    building = _create_building(client, admin_headers)
    response = client.get(f"/api/buildings/{building['id']}/energy")
    assert response.status_code == 401


def test_auditor_can_add_energy(client, auditor_headers):
    building = _create_building(client, auditor_headers, name="Auditor Block")
    response = _add(client, auditor_headers, building["id"])
    assert response.status_code == 201


def test_duplicate_month_rejected(client, admin_headers):
    building = _create_building(client, admin_headers)
    assert _add(client, admin_headers, building["id"], month="2025-01").status_code == 201
    response = _add(client, admin_headers, building["id"], month="2025-01", kwh=5, cost=5)
    assert response.status_code == 409


def test_negative_values_rejected(client, admin_headers):
    building = _create_building(client, admin_headers)

    negative_kwh = _add(client, admin_headers, building["id"], month="2025-01", kwh=-1)
    assert negative_kwh.status_code == 400

    negative_cost = _add(client, admin_headers, building["id"], month="2025-02", cost=-1)
    assert negative_cost.status_code == 400


def test_bad_month_rejected(client, admin_headers):
    building = _create_building(client, admin_headers)
    response = _add(client, admin_headers, building["id"], month="2025-13")
    assert response.status_code == 400


def test_update_and_delete_record(client, admin_headers):
    building = _create_building(client, admin_headers)
    record = _add(client, admin_headers, building["id"]).get_json()["data"]
    base = f"/api/buildings/{building['id']}/energy/{record['id']}"

    updated = client.patch(base, headers=admin_headers, json={"kwh": 999, "month": "2025-03"})
    assert updated.status_code == 200
    data = updated.get_json()["data"]
    assert data["kwh"] == 999.0
    assert data["month"] == "2025-03"

    deleted = client.delete(base, headers=admin_headers)
    assert deleted.status_code == 200
    assert client.get(
        f"/api/buildings/{building['id']}/energy", headers=admin_headers
    ).get_json()["data"] == []


def test_cross_tenant_energy_is_404(client, admin_headers):
    building = _create_building(client, admin_headers)
    record = _add(client, admin_headers, building["id"]).get_json()["data"]
    other = _other_headers(client)

    assert client.get(
        f"/api/buildings/{building['id']}/energy", headers=other
    ).status_code == 404
    assert _add(client, other, building["id"], month="2025-09").status_code == 404
    assert client.patch(
        f"/api/buildings/{building['id']}/energy/{record['id']}",
        headers=other,
        json={"kwh": 1},
    ).status_code == 404
    assert client.delete(
        f"/api/buildings/{building['id']}/energy/{record['id']}", headers=other
    ).status_code == 404
    assert client.post(
        f"/api/buildings/{building['id']}/energy/import",
        headers=other,
        json={"csv": CSV_OK, "confirm": True},
    ).status_code == 404


def test_import_dry_run_requires_confirmation(client, admin_headers):
    building = _create_building(client, admin_headers)

    response = client.post(
        f"/api/buildings/{building['id']}/energy/import",
        headers=admin_headers,
        json={"csv": CSV_OK},
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["valid_rows"] == 2
    assert data["imported"] == 0
    assert data["requires_confirmation"] is True
    assert data["errors"] == []

    assert client.get(
        f"/api/buildings/{building['id']}/energy", headers=admin_headers
    ).get_json()["data"] == []


def test_import_confirm_imports_valid_rows(client, admin_headers):
    building = _create_building(client, admin_headers)

    response = client.post(
        f"/api/buildings/{building['id']}/energy/import",
        headers=admin_headers,
        json={"csv": CSV_OK, "confirm": True},
    )
    data = response.get_json()["data"]
    assert data["imported"] == 2
    assert data["valid_rows"] == 2
    assert "requires_confirmation" not in data

    listing = client.get(
        f"/api/buildings/{building['id']}/energy", headers=admin_headers
    ).get_json()["data"]
    assert [row["month"] for row in listing] == ["2025-01", "2025-02"]


def test_import_reports_bad_rows(client, admin_headers):
    building = _create_building(client, admin_headers)
    csv_text = (
        "month,kwh,cost\n"
        "2025-01,1000,2000\n"
        "2025-13,100,200\n"
        "2025-02,-5,200\n"
        "2025-03,abc,xyz\n"
    )

    response = client.post(
        f"/api/buildings/{building['id']}/energy/import",
        headers=admin_headers,
        json={"csv": csv_text, "confirm": True},
    )
    data = response.get_json()["data"]
    assert data["imported"] == 1
    assert [row["row"] for row in data["errors"]] == [3, 4, 5]


def test_import_flags_existing_and_duplicate_months(client, admin_headers):
    building = _create_building(client, admin_headers)
    assert _add(client, admin_headers, building["id"], month="2025-01").status_code == 201

    csv_text = (
        "month,kwh,cost\n"
        "2025-01,1000,2000\n"
        "2025-02,1,2\n"
        "2025-02,3,4\n"
    )
    response = client.post(
        f"/api/buildings/{building['id']}/energy/import",
        headers=admin_headers,
        json={"csv": csv_text, "confirm": True},
    )
    data = response.get_json()["data"]
    assert data["imported"] == 1
    assert {row["row"] for row in data["errors"]} == {2, 4}


def test_import_bad_header_reports_row_one(client, admin_headers):
    building = _create_building(client, admin_headers)

    response = client.post(
        f"/api/buildings/{building['id']}/energy/import",
        headers=admin_headers,
        json={"csv": "month,energy\n2025-01,1000\n", "confirm": True},
    )
    data = response.get_json()["data"]
    assert data["imported"] == 0
    assert data["errors"][0]["row"] == 1
