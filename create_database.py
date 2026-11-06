import os
from urllib.parse import unquote, urlparse

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = "mysql+mysqlconnector://root:root@localhost:3306/energy_audit"


def _parse_database_url(database_url: str) -> dict:
    parsed = urlparse(database_url)
    return {
        "database": (parsed.path or "").lstrip("/") or "energy_audit",
        "user": parsed.username or "root",
        "password": unquote(parsed.password or ""),
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
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
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    database_name = create_database(database_url)
    print(f"Database '{database_name}' is ready.")


if __name__ == "__main__":
    main()
