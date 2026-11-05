OTHER_REGISTER = {
    "institution_name": "Other Institute",
    "admin_name": "Other Admin",
    "admin_email": "other@test.org",
    "password": "password123",
}


def _create_user(client, headers, email="newaud@test.org"):
    return client.post(
        "/api/users",
        headers=headers,
        json={"name": "New Auditor", "email": email, "password": "password123"},
    )


def test_admin_lists_users(client, admin_headers):
    res = client.get("/api/users", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data) == 1
    assert data[0]["role"] == "admin"


def test_auditor_cannot_list_users(client, auditor_headers):
    res = client.get("/api/users", headers=auditor_headers)
    assert res.status_code == 403


def test_admin_creates_auditor_with_temp_password(client, admin_headers):
    res = _create_user(client, admin_headers)
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["role"] == "auditor"
    assert data["must_change_password"] is True


def test_duplicate_email_rejected(client, admin_headers):
    _create_user(client, admin_headers)
    res = _create_user(client, admin_headers)
    assert res.status_code == 409


def test_invalid_user_email_rejected(client, admin_headers):
    res = client.post(
        "/api/users",
        headers=admin_headers,
        json={"name": "Bad", "email": "not-an-email", "password": "password123"},
    )
    assert res.status_code == 400


def test_admin_updates_user(client, admin_headers):
    created = _create_user(client, admin_headers).get_json()["data"]
    res = client.patch(
        f"/api/users/{created['id']}",
        headers=admin_headers,
        json={"name": "Renamed Auditor", "password": "newpassword1"},
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["name"] == "Renamed Auditor"
    assert data["must_change_password"] is True


def test_admin_deletes_user(client, admin_headers):
    created = _create_user(client, admin_headers).get_json()["data"]
    res = client.delete(f"/api/users/{created['id']}", headers=admin_headers)
    assert res.status_code == 200
    remaining = client.get("/api/users", headers=admin_headers).get_json()["data"]
    assert len(remaining) == 1


def test_admin_cannot_delete_self(client, admin_headers, registered):
    res = client.delete(f"/api/users/{registered['user_id']}", headers=admin_headers)
    assert res.status_code == 409


def test_cross_tenant_user_is_not_found(client, admin_headers):
    other = client.post(
        "/api/auth/register-institution",
        json=OTHER_REGISTER,
    ).get_json()["data"]
    res = client.delete(f"/api/users/{other['user_id']}", headers=admin_headers)
    assert res.status_code == 404
