import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("JWT_SECRET", "dev-jwt-secret-change-me-in-production-please")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+mysqlconnector://root:root@localhost:3306/energy_audit",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION_SECONDS = int(os.environ.get("JWT_EXPIRATION_SECONDS", "3600"))
    BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
    ALLOWED_ORIGINS = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
