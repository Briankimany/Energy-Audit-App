from flask import Flask, request

from server import config, errors, extensions, logging
from server.blueprints import auth_bp
from server.responses import error_response


def create_app(config_object: str = "server.config.DevelopmentConfig"):
    app = Flask(__name__)
    app.config.from_object(config_object)
    extensions.db.init_app(app)

    errors.register_error_handlers(app)
    logging.register_error_logger(app)

    app.register_blueprint(auth_bp)

    @app.before_request
    def enforce_origin():
        origin = request.headers.get("Origin")
        allowed = app.config.get("ALLOWED_ORIGINS") or []
        if origin and origin not in allowed:
            return error_response("origin not allowed", status_code=403)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        extensions.db.session.remove()

    return app
