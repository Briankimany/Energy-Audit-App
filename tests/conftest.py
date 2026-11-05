import pytest
from flask import Blueprint

from server import create_app, extensions
from server.errors import BusinessError


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
