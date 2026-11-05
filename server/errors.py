from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    status_code = 400

    def __init__(self, message: str, errors: dict | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}


class ValidationError(ApiError):
    status_code = 400


class BusinessError(ApiError):
    status_code = 409


class NotFoundError(ApiError):
    status_code = 404


class UnauthorizedError(ApiError):
    status_code = 401


class ForbiddenError(ApiError):
    status_code = 403


def register_error_handlers(app) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        return (
            jsonify({"status": exc.status_code, "message": exc.message, "errors": exc.errors}),
            exc.status_code,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return (
            jsonify({"status": exc.code, "message": exc.description, "errors": {}}),
            exc.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        app.logger.exception("unexpected error")
        return (
            jsonify({"status": 500, "message": "internal server error", "errors": {}}),
            500,
        )
