def test_business_error_returns_envelope(error_client):
    res = error_client.get("/api/_test/business-error")
    assert res.status_code == 409
    assert res.get_json() == {"status": 409, "message": "boom", "errors": {}}


def test_unexpected_error_returns_safe_envelope(error_client):
    res = error_client.get("/api/_test/unexpected-error")
    assert res.status_code == 500
    assert res.get_json() == {
        "status": 500,
        "message": "internal server error",
        "errors": {},
    }
