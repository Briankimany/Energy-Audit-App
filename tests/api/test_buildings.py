BUILDING = {
    "name": "Main Block",
    "type": "office",
    "floor_area_m2": 250,
    "operating_hours": 9,
}

OTHER_REGISTER = {
    "institution_name": "Other Institute",
    "admin_name": "Other Admin",
    "admin_email": "other@test.org",
    "password": "password123",
}


def test_create_and_list_buildings(client, admin_headers):
    res = client.post("/api/buildings", headers=admin_headers, json=BUILDING)
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["name"] == "Main Block"
    assert data["floor_area_m2"] == 250.0

    listing = client.get("/api/buildings", headers=admin_headers).get_json()["data"]
    assert len(listing) == 1


def test_buildings_require_auth(client):
    assert client.get("/api/buildings").status_code == 401


def test_auditor_can_create_building(client, auditor_headers):
    res = client.post("/api/buildings", headers=auditor_headers, json=BUILDING)
    assert res.status_code == 201


def test_duplicate_building_name_rejected(client, admin_headers):
    client.post("/api/buildings", headers=admin_headers, json=BUILDING)
    res = client.post("/api/buildings", headers=admin_headers, json=BUILDING)
    assert res.status_code == 409


def test_floor_area_must_be_positive(client, admin_headers):
    res = client.post(
        "/api/buildings",
        headers=admin_headers,
        json={**BUILDING, "floor_area_m2": 0},
    )
    assert res.status_code == 400


def test_operating_hours_must_be_in_range(client, admin_headers):
    res = client.post(
        "/api/buildings",
        headers=admin_headers,
        json={**BUILDING, "operating_hours": 25},
    )
    assert res.status_code == 400


def test_building_limit_is_enforced(client, admin_headers):
    client.patch("/api/institution", headers=admin_headers, json={"max_buildings": 1})
    client.post("/api/buildings", headers=admin_headers, json=BUILDING)
    res = client.post(
        "/api/buildings",
        headers=admin_headers,
        json={**BUILDING, "name": "Second Block"},
    )
    assert res.status_code == 409


def test_update_and_delete_building(client, admin_headers):
    created = client.post(
        "/api/buildings", headers=admin_headers, json=BUILDING
    ).get_json()["data"]

    res = client.patch(
        f"/api/buildings/{created['id']}",
        headers=admin_headers,
        json={"name": "Renamed Block", "operating_hours": 10},
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["name"] == "Renamed Block"

    assert client.delete(
        f"/api/buildings/{created['id']}", headers=admin_headers
    ).status_code == 200
    assert client.get(
        f"/api/buildings/{created['id']}", headers=admin_headers
    ).status_code == 404


def test_cross_tenant_building_is_404(client, admin_headers):
    created = client.post(
        "/api/buildings", headers=admin_headers, json=BUILDING
    ).get_json()["data"]
    other = client.post(
        "/api/auth/register-institution", json=OTHER_REGISTER
    ).get_json()["data"]
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    assert client.get(
        f"/api/buildings/{created['id']}", headers=other_headers
    ).status_code == 404
    assert client.patch(
        f"/api/buildings/{created['id']}",
        headers=other_headers,
        json={"name": "Hijacked"},
    ).status_code == 404
    assert client.delete(
        f"/api/buildings/{created['id']}", headers=other_headers
    ).status_code == 404
