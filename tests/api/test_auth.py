from server import extensions
from server.models.user import User


def _register(client, **overrides):
    payload = {
        "institution_name": "Test Institute",
        "admin_name": "Admin User",
        "admin_email": "admin@test.org",
        "password": "password123",
    }
    payload.update(overrides)
    return client.post("/api/auth/register-institution", json=payload)


def test_register_institution_creates_admin_and_token(client):
    res = _register(client)
    assert res.status_code == 201
    body = res.get_json()
    assert body["status"] == "success"
    assert body["data"]["institution_id"] > 0
    assert body["data"]["user_id"] > 0
    assert body["data"]["access_token"]


def test_register_commits_work(app, client):
    _register(client)
    with app.app_context():
        extensions.db.session.remove()
        assert extensions.db.session.query(User).count() == 1


def test_register_duplicate_email_conflicts(client):
    _register(client)
    res = _register(client, institution_name="Other Institute")
    assert res.status_code == 409
    assert res.get_json()["status"] == 409


def test_login_success_returns_token(client):
    _register(client)
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@test.org", "password": "password123"},
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["token_type"] == "Bearer"
    assert data["access_token"]


def test_login_wrong_password_rejected(client):
    _register(client)
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@test.org", "password": "wrongpass1"},
    )
    assert res.status_code == 401
    assert res.get_json()["errors"] == {}


def test_logout_requires_token(client):
    res = client.post("/api/auth/logout")
    assert res.status_code == 401


def test_logout_with_token_succeeds(client):
    token = _register(client).get_json()["data"]["access_token"]
    res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"


def test_change_password_requires_token(client):
    res = client.post(
        "/api/auth/change-password",
        json={"current_password": "password123", "new_password": "newpassword1"},
    )
    assert res.status_code == 401


def test_change_password_updates_credentials(client):
    token = _register(client).get_json()["data"]["access_token"]
    res = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "password123", "new_password": "newpassword1"},
    )
    assert res.status_code == 200

    old = client.post(
        "/api/auth/login",
        json={"email": "admin@test.org", "password": "password123"},
    )
    assert old.status_code == 401

    new = client.post(
        "/api/auth/login",
        json={"email": "admin@test.org", "password": "newpassword1"},
    )
    assert new.status_code == 200
