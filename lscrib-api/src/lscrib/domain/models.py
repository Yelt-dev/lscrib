"""Enums y esquemas de dominio. Fuente de verdad de la máquina de estados."""

from enum import Enum

from pydantic import BaseModel


class JobStatus(str, Enum):
    """Estados del Job en su máquina de estados."""

    UPLOADED = "uploaded"        # archivo recibido, hash calculado
    QUEUED = "queued"            # esperando turno (uno a la vez)
    NORMALIZING = "normalizing"  # ffmpeg → wav 16 kHz mono
    TRANSCRIBING = "transcribing"  # faster-whisper trabajando
    COMPLETED = "completed"      # transcript listo
    FAILED = "failed"            # error
    CANCELED = "canceled"        # cancelado por el usuario


# transiciones permitidas. Se validan en el worker antes de mover estado.
ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.UPLOADED: {JobStatus.QUEUED},
    JobStatus.QUEUED: {JobStatus.NORMALIZING, JobStatus.CANCELED},
    JobStatus.NORMALIZING: {JobStatus.TRANSCRIBING, JobStatus.FAILED, JobStatus.CANCELED},
    JobStatus.TRANSCRIBING: {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED},
    JobStatus.COMPLETED: set(),  # terminal (editar texto no cambia estado)
    JobStatus.FAILED: {JobStatus.QUEUED},    # reintentar
    JobStatus.CANCELED: {JobStatus.QUEUED},  # reencolar
}


def can_transition(src: JobStatus, dst: JobStatus) -> bool:
    return dst in ALLOWED_TRANSITIONS[src]


class MediaType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"


class WordTS(BaseModel):
    """Timestamp por palabra, guardado como JSON en Segment."""

    w: str
    start_ms: int
    end_ms: int
    p: float | None = None  # confianza 0–1 del modelo (para resaltar dudosas)


class SegmentRead(BaseModel):
    index: int
    start_ms: int
    end_ms: int
    text: str
    words: list[WordTS] | None = None


class JobRead(BaseModel):
    id: str
    original_filename: str
    media_type: MediaType
    duration_sec: int | None = None
    language: str | None = None
    model: str
    prompt: str | None = None
    status: JobStatus
    progress: float = 0.0
    position: int = 0            # orden en la cola (para reordenar en la UI)
    error: str | None = None


class JobDetail(JobRead):
    """Job + sus segmentos (para la vista de transcript)."""

    segments: list[SegmentRead] = []
