def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Energy Monitor" in response.data


def test_register_page_renders(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create your institution" in response.data


def test_compare_page_renders(client):
    response = client.get("/analysis/compare")
    assert response.status_code == 200
    assert b"compareChart" in response.data
    assert b"compare-table" in response.data


def test_energy_page_renders_analysis_controls(client):
    response = client.get("/buildings/1/energy")
    assert response.status_code == 200
    assert b"buildingEnergyChart" in response.data
    assert b"analysis-kwh" in response.data
    assert b"load-sample-csv" in response.data
    assert b"standard-rate-note" in response.data


def test_settings_page_renders_standard_rate(client):
    response = client.get("/settings")
    assert response.status_code == 200
    assert b"standard_cost_per_kwh" in response.data


def test_dashboard_renders_when_anonymous(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"dashboard-root" in response.data
    assert b"stat-kwh" in response.data
    assert b"consumptionChart" in response.data
    assert b"anomaly-list" in response.data


def test_dashboard_renders_when_authenticated(client, admin_headers):
    response = client.get("/dashboard", headers=admin_headers)
    assert response.status_code == 200
    assert b"dashboard-root" in response.data
    assert b"stat-cost" in response.data
