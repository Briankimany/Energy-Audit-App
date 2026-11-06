import os
from urllib.parse import unquote, quote_plus, urlparse

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MYSQL_HOST = "127.0.0.1"
DEFAULT_MYSQL_PORT = "3306"
DEFAULT_MYSQL_USER = "root"
DEFAULT_MYSQL_PASSWORD = "root"
DEFAULT_MYSQL_DATABASE = "energy_audit"


def build_database_url() -> str:
    host = os.environ.get("MYSQL_HOST", DEFAULT_MYSQL_HOST)
    port = os.environ.get("MYSQL_PORT", DEFAULT_MYSQL_PORT)
    user = os.environ.get("MYSQL_USER", DEFAULT_MYSQL_USER)
    password = os.environ.get("MYSQL_PASSWORD", DEFAULT_MYSQL_PASSWORD)
    database = os.environ.get("MYSQL_DATABASE", DEFAULT_MYSQL_DATABASE)
    return f"mysql+mysqlconnector://{user}:{quote_plus(password)}@{host}:{port}/{database}"


def _parse_database_url(database_url: str) -> dict:
    parsed = urlparse(database_url)
    return {
        "database": (parsed.path or "").lstrip("/") or DEFAULT_MYSQL_DATABASE,
        "user": parsed.username or DEFAULT_MYSQL_USER,
        "password": unquote(parsed.password or DEFAULT_MYSQL_PASSWORD),
        "host": parsed.hostname or DEFAULT_MYSQL_HOST,
        "port": parsed.port or int(DEFAULT_MYSQL_PORT),
    }


def create_database(database_url: str) -> str:
    config = _parse_database_url(database_url)
    connection = mysql.connector.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
    )
    try:
        cursor = connection.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{config['database']}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.execute(f"USE `{config['database']}`")
        connection.commit()
        cursor.close()
    finally:
        connection.close()
    return config["database"]


def main() -> None:
    database_name = create_database(build_database_url())
    print(f"Database '{database_name}' is ready.")


if __name__ == "__main__":
    main()
