"""Entorno Alembic. Usa el mismo engine/URL y metadata que la app."""

from alembic import context
from sqlmodel import SQLModel

from lscrib.config import settings
from lscrib.db.session import engine

# Registra los modelos en SQLModel.metadata (autogenerate compara contra esto).
import lscrib.db.models  # noqa: F401,E402

config = context.config
config.set_main_option("sqlalchemy.url", settings.db_url)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,  # SQLite: ALTER TABLE vía tabla temporal
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite no soporta ALTER nativo completo
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
