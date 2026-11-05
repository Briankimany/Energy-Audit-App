BUILDING = {
    "name": "Main Block",
    "type": "office",
    "floor_area_m2": 250,
    "operating_hours": 9,
}


def test_get_institution(client, admin_headers):
    res = client.get("/api/institution", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["name"] == "Test Institute"
    assert data["currency"] == "KES"
    assert data["max_buildings"] == 5


def test_get_institution_requires_auth(client):
    assert client.get("/api/institution").status_code == 401


def test_admin_updates_institution(client, admin_headers):
    res = client.patch(
        "/api/institution",
        headers=admin_headers,
        json={"name": "Renamed Institute", "currency": "usd", "max_buildings": 10},
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["name"] == "Renamed Institute"
    assert data["currency"] == "USD"
    assert data["max_buildings"] == 10


def test_auditor_cannot_update_institution(client, auditor_headers):
    res = client.patch("/api/institution", headers=auditor_headers, json={"name": "Nope"})
    assert res.status_code == 403


def test_invalid_currency_rejected(client, admin_headers):
    res = client.patch("/api/institution", headers=admin_headers, json={"currency": "us"})
    assert res.status_code == 400


def test_invalid_max_buildings_rejected(client, admin_headers):
    res = client.patch("/api/institution", headers=admin_headers, json={"max_buildings": 0})
    assert res.status_code == 400


def test_max_buildings_cannot_drop_below_building_count(client, admin_headers):
    for name in ("Block A", "Block B"):
        client.post("/api/buildings", headers=admin_headers, json={**BUILDING, "name": name})
    res = client.patch("/api/institution", headers=admin_headers, json={"max_buildings": 1})
    assert res.status_code == 409
