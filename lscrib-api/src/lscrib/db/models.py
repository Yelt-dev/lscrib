"""Tablas SQLModel. Espejo del modelo conceptual (doc 05)."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, Relationship, SQLModel

from lscrib.domain.models import JobStatus, MediaType


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Job(SQLModel, table=True):
    """Un archivo subido + su transcripción. Entidad central (doc 05)."""

    id: str = Field(default_factory=_uuid, primary_key=True)
    original_filename: str
    file_hash: str = Field(index=True)          # SHA-256 → idempotencia (R9)
    media_path: str                              # ruta del wav normalizado
    duration_sec: int | None = None
    media_type: MediaType
    language: str | None = None                  # null hasta detectar (R10)
    model: str
    status: JobStatus = JobStatus.UPLOADED
    progress: float = 0.0                        # 0.0–1.0 (barra en vivo)
    position: int = Field(default=0, index=True)  # orden en la cola (reordenable, R7)
    error: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = None

    segments: list["Segment"] = Relationship(back_populates="job")


class Segment(SQLModel, table=True):
    """Trozo de texto con su ventana temporal. Un Job tiene muchos Segment."""

    id: str = Field(default_factory=_uuid, primary_key=True)
    job_id: str = Field(foreign_key="job.id", index=True)
    index: int
    start_ms: int
    end_ms: int
    text: str                                    # editable por el usuario
    # timestamps por palabra (R11) como JSON; evita una tabla Word enorme (doc 05)
    words: list | None = Field(default=None, sa_column=Column(JSON))

    job: Job | None = Relationship(back_populates="segments")


class Settings(SQLModel, table=True):
    """Preferencias (fila única / singleton)."""

    id: int = Field(default=1, primary_key=True)
    default_model: str = "small"
    default_language: str | None = "auto"
    max_file_mb: int = 2048
    theme: str = "system"  # light | dark | system
