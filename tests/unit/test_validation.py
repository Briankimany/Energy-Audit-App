def test_non_json_content_type_rejected(client):
    res = client.post("/api/auth/login", data="email=x", content_type="text/plain")
    assert res.status_code == 400
    assert "body" in res.get_json()["errors"]


def test_json_array_rejected(client):
    res = client.post("/api/auth/login", json=["not", "an", "object"])
    assert res.status_code == 400
    assert "body" in res.get_json()["errors"]


def test_missing_fields_rejected(client):
    res = client.post("/api/auth/login", json={"email": "a@b.co"})
    assert res.status_code == 400
    assert res.get_json()["errors"]["fields"] == ["password"]


def test_short_password_rejected(client):
    res = client.post(
        "/api/auth/register-institution",
        json={
            "institution_name": "X",
            "admin_name": "Y",
            "admin_email": "a@b.co",
            "password": "short",
        },
    )
    assert res.status_code == 400
    assert "password" in res.get_json()["errors"]


def test_valid_payload_passes_boundary(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert res.status_code == 401
