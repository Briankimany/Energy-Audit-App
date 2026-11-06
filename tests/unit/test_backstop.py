def test_unknown_origin_is_refused(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "a@b.co", "password": "password123"},
        headers={"Origin": "http://evil.example.com"},
    )
    assert res.status_code == 403
    assert res.get_json()["status"] == 403


def test_allowed_origin_passes_backstop(client):
    client.application.config["ALLOWED_ORIGINS"] = ["http://localhost:5173"]
    res = client.post(
        "/api/auth/login",
        json={"email": "a@b.co", "password": "password123"},
        headers={"Origin": "http://localhost:5173"},
    )
    assert res.status_code == 401
