"""Migraciones Alembic en runtime.

La app es local-first: cada usuario tiene su propia SQLite y no hay un DBA que
corra `alembic upgrade` a mano. Por eso las migraciones se aplican solas al
arrancar. Construimos la Config en código (no leemos `alembic.ini`) para
localizar las migraciones dentro del paquete instalado y usar la misma URL que
`settings`.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from lscrib.config import settings
from lscrib.db.session import engine

_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _config() -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", settings.db_url)
    return cfg


def _has_legacy_schema() -> bool:
    """True si la BD ya tiene nuestras tablas pero nunca pasó por Alembic.

    Es el caso de las BD creadas con `create_all` antes de introducir
    migraciones (dev/beta). Las marcamos en la baseline en vez de recrearlas.
    """
    tables = set(inspect(engine).get_table_names())
    return "job" in tables and "alembic_version" not in tables


def run_migrations() -> None:
    """Deja la BD en `head`. Idempotente: seguro en cada arranque."""
    cfg = _config()
    if _has_legacy_schema():
        # BD preexistente sin control de versiones: asúmela en la baseline
        # (0001) para no chocar con `CREATE TABLE` de tablas que ya existen.
        command.stamp(cfg, "0001")
    command.upgrade(cfg, "head")
