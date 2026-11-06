# Energy-Audit-App

## Tech Stack

- **Frontend:** Vanilla JavaScript with server-rendered Jinja2 templates via Flask, no SPA and no framework. Plain CSS. Charts via Chart.js / canvas.
- **Backend:** Python 3, Flask, SQLAlchemy, PyJWT, bcrypt, mysql-connector.
- **Database:** MySQL.

## Local Setup

1. Create a virtual environment and install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and set the `MYSQL_*` credentials, `JWT_SECRET`, and `CORS_ORIGINS`.
3. Create the MySQL database: `"venv\Scripts\python.exe" create_database.py`
4. Apply migrations: `"venv\Scripts\python.exe" -m alembic upgrade head`
5. Run tests: `"venv\Scripts\python.exe" -m pytest -q`
6. Start the server: `"venv\Scripts\python.exe" run.py`

`CORS_ORIGINS` must include the origin you open in the browser (for example `http://127.0.0.1:5000`) because browsers send an `Origin` header on same-origin state-changing requests.

## Documentation

- [Simplified architecture for presentations](./docs/simplified-architecture.md)
- [Architecture and information flow](./docs/architecture.md)
- [API contract](./docs/api.md)
- [Analysis formulas](./docs/formulas.md)
- [What has been built](./docs/what-has-been-built.md)
- [Phase tracking](./PHASE_TRACK.md)
