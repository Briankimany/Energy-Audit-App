import mysql.connector

from server.config import _parse_database_url, build_database_url


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
