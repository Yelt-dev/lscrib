"""Configuración central. Sobrescribible por entorno (prefijo `LSCRIB_`)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LSCRIB_", env_file=".env")

    # red / servidor
    host: str = "127.0.0.1"
    port: int = 8000

    # almacenamiento local (local-first, R1)
    data_dir: Path = Path("./data")        # medios subidos + artefactos
    db_path: Path = Path("./lscrib.db")    # metadatos (SQLite)

    # límites (R15): tope por defecto ~2 GB, ajustable por entorno
    max_file_mb: int = 2048

    # transcripción
    default_model: str = "small"     # ver lscrib.models.registry
    default_language: str = "auto"   # autodetección con override (R10)
    compute_type: str = "auto"       # CPU/GPU; degrada con claridad (R14)

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"


settings = Settings()
