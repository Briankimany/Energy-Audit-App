import pytest
from flask import Blueprint

from server import create_app, extensions
from server.errors import BusinessError

REGISTER_PAYLOAD = {
    "institution_name": "Test Institute",
    "admin_name": "Admin User",
    "admin_email": "admin@test.org",
    "password": "password123",
}


@pytest.fixture()
def app():
    application = create_app(config_object="server.config.TestingConfig")
    with application.app_context():
        extensions.db.create_all()
        yield application
        extensions.db.session.remove()
        extensions.db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def error_client(app):
    probe = Blueprint("error_probe", __name__)

    @probe.get("/api/_test/business-error")
    def raise_business_error():
        raise BusinessError("boom")

    @probe.get("/api/_test/unexpected-error")
    def raise_unexpected_error():
        raise RuntimeError("kaboom")

    app.register_blueprint(probe)
    return app.test_client()


@pytest.fixture()
def registered(client):
    res = client.post("/api/auth/register-institution", json=REGISTER_PAYLOAD)
    return res.get_json()["data"]


@pytest.fixture()
def admin_headers(registered):
    return {"Authorization": f"Bearer {registered['access_token']}"}


@pytest.fixture()
def auditor_headers(client, admin_headers):
    client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "name": "Auditor User",
            "email": "auditor@test.org",
            "password": "password123",
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "auditor@test.org", "password": "password123"},
    )
    return {"Authorization": f"Bearer {res.get_json()['data']['access_token']}"}
