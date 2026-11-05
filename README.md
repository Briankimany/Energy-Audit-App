# Energy-Audit-App

## Tech Stack

- **Frontend:** Vanilla JavaScript (ES modules) with server-rendered Jinja2 templates via Flask — no SPA, no framework. Plain CSS. Charts via Chart.js / canvas.
- **Backend:** Python 3, Flask, SQLAlchemy, PyJWT, bcrypt, WeasyPrint, mysql-connector.
- **Database:** MySQL.

## Local Setup

1. Create a MySQL database (for example `energy_audit`).
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `DATABASE_URL` and `JWT_SECRET`.
4. Create tables: `python -c "from server import create_app, extensions; app = create_app(); app.app_context().push(); extensions.db.create_all()"`
5. Run tests: `pytest`
6. Start the server: `python run.py`

## Phase Tracking

See [PHASE_TRACK.md](./PHASE_TRACK.md).
