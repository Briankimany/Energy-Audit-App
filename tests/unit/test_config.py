def test_testing_config_is_loaded(app):
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite")
    assert app.config["JWT_EXPIRATION_SECONDS"] > 0
    assert isinstance(app.config["ALLOWED_ORIGINS"], list)
    assert app.config["ALLOWED_ORIGINS"]
