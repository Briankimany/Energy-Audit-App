import os
from urllib.parse import quote_plus, unquote, urlparse

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MYSQL_HOST = "127.0.0.1"
DEFAULT_MYSQL_PORT = "3306"
DEFAULT_MYSQL_USER = "root"
DEFAULT_MYSQL_PASSWORD = "root"
DEFAULT_MYSQL_DATABASE = "energy_audit"


def _parse_database_url(database_url: str) -> dict:
    parsed = urlparse(database_url)
    return {
        "database": (parsed.path or "").lstrip("/") or DEFAULT_MYSQL_DATABASE,
        "user": parsed.username or DEFAULT_MYSQL_USER,
        "password": unquote(parsed.password or DEFAULT_MYSQL_PASSWORD),
        "host": parsed.hostname or DEFAULT_MYSQL_HOST,
        "port": parsed.port or int(DEFAULT_MYSQL_PORT),
    }


def build_database_url() -> str:
    host = os.environ.get("MYSQL_HOST", DEFAULT_MYSQL_HOST)
    port = os.environ.get("MYSQL_PORT", DEFAULT_MYSQL_PORT)
    user = os.environ.get("MYSQL_USER", DEFAULT_MYSQL_USER)
    password = os.environ.get("MYSQL_PASSWORD", DEFAULT_MYSQL_PASSWORD)
    database = os.environ.get("MYSQL_DATABASE", DEFAULT_MYSQL_DATABASE)
    return f"mysql+mysqlconnector://{user}:{quote_plus(password)}@{host}:{port}/{database}"


class Config:
    SECRET_KEY = os.environ.get("JWT_SECRET", "dev-jwt-secret-change-me-in-production-please")
    SQLALCHEMY_DATABASE_URI = build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION_SECONDS = int(os.environ.get("JWT_EXPIRATION_SECONDS", "3600"))
    BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
    ALLOWED_ORIGINS = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "").split(",")
        if o.strip()
    ]


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
