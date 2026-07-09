"""Transcripción con faster-whisper: wav → segmentos con timestamps.

Corre en CPU y aprovecha Apple Silicon. El modelo se descarga bajo demanda la
primera vez (R2) y queda en caché local.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from lscrib.config import settings

# Cargar un WhisperModel es caro (lee pesos de disco). Se cachea por
# (nombre, compute_type) para reusarlo entre trabajos secuenciales (R7).
_MODELS: dict[tuple[str, str], object] = {}


@dataclass
class TranscribedSegment:
    """Salida normalizada del motor → se mapea a db.models.Segment."""

    index: int
    start_ms: int
    end_ms: int
    text: str
    words: list[dict] | None = None  # [{w, start_ms, end_ms}] si el modelo los da (R11)


@dataclass
class Transcription:
    """Handle de una transcripción en curso.

    `language` está disponible de inmediato (autodetección, R10); `segments` es
    perezoso: iterarlo dispara el cómputo real y permite reportar progreso en
    vivo (doc 07: progress = end_actual / duración_total).
    """

    language: str
    duration_sec: float
    segments: Iterator[TranscribedSegment] = field(repr=False)


def _resolve_compute_type() -> str:
    """`auto` → int8 (rápido y suficiente en CPU/Apple Silicon, doc 08)."""
    ct = settings.compute_type
    return "int8" if ct == "auto" else ct


def _get_model(name: str):
    from faster_whisper import WhisperModel

    key = (name, _resolve_compute_type())
    model = _MODELS.get(key)
    if model is None:
        # device="auto": CUDA si hay, si no CPU (R14: degradar con claridad).
        model = WhisperModel(name, device="auto", compute_type=key[1])
        _MODELS[key] = model
    return model


def transcribe(
    audio_path: Path,
    model: str,
    language: str | None = None,
) -> Transcription:
    """Transcribe `audio_path`. `language=None` → autodetección (R10).

    Devuelve un `Transcription` con el idioma detectado y un iterador perezoso
    de segmentos. La descarga del modelo ocurre dentro de `_get_model` la
    primera vez (R2).
    """
    whisper_model = _get_model(model)
    segments, info = whisper_model.transcribe(
        str(audio_path),
        language=language,
        word_timestamps=True,
    )

    def _iter() -> Iterator[TranscribedSegment]:
        for i, s in enumerate(segments):
            words = None
            if s.words:
                words = [
                    {
                        "w": w.word,
                        "start_ms": int(w.start * 1000),
                        "end_ms": int(w.end * 1000),
                        # confianza 0–1 del modelo; alimenta el resaltado de dudosas
                        "p": round(float(w.probability), 3)
                        if w.probability is not None
                        else None,
                    }
                    for w in s.words
                ]
            yield TranscribedSegment(
                index=i,
                start_ms=int(s.start * 1000),
                end_ms=int(s.end * 1000),
                text=s.text.strip(),
                words=words,
            )

    return Transcription(
        language=info.language,
        duration_sec=info.duration,
        segments=_iter(),
    )
