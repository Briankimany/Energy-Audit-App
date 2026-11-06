from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from server import create_app, extensions
from server.config import build_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

app = create_app()
target_metadata = extensions.db.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=build_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with app.app_context():
        with extensions.db.engine.begin() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
