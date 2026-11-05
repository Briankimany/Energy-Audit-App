from flask import jsonify


def success_response(message: str, data=None, meta=None, status_code: int = 200):
    body = {"status": "success", "message": message, "data": data}
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status_code


def error_response(message: str, errors=None, status_code: int = 400):
    return (
        jsonify({"status": status_code, "message": message, "errors": errors or {}}),
        status_code,
    )
