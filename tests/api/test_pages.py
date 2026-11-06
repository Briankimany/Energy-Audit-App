def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Energy Audit" in response.data


def test_register_page_renders(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create your institution" in response.data


def test_dashboard_redirects_when_anonymous(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_dashboard_renders_when_authenticated(client, admin_headers):
    response = client.get("/dashboard", headers=admin_headers)
    assert response.status_code == 200
    assert b"Welcome to the" in response.data
