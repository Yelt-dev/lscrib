"""Exports deterministas: segments → SRT / VTT / TXT / MD (R12).

Funciones puras y testeables sin correr Whisper. Deterministas: el mismo
transcript da siempre el mismo archivo, sin marcas de tiempo de generación que
ensucien diffs (R12).
"""

from typing import Protocol


class SegmentLike(Protocol):
    """Lo mínimo que un render necesita de un segmento (db.models.Segment lo cumple)."""

    index: int
    start_ms: int
    end_ms: int
    text: str


def _clock(ms: int, sep: str) -> str:
    """ms → `HH:MM:SS<sep>mmm`. `sep` es `,` para SRT y `.` para VTT."""
    ms = max(0, ms)
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{sep}{millis:03d}"


def to_srt(segments: list[SegmentLike]) -> str:
    blocks = []
    for n, s in enumerate(segments, start=1):
        blocks.append(
            f"{n}\n"
            f"{_clock(s.start_ms, ',')} --> {_clock(s.end_ms, ',')}\n"
            f"{s.text.strip()}\n"
        )
    return "\n".join(blocks)


def to_vtt(segments: list[SegmentLike]) -> str:
    blocks = ["WEBVTT\n"]
    for s in segments:
        blocks.append(
            f"{_clock(s.start_ms, '.')} --> {_clock(s.end_ms, '.')}\n"
            f"{s.text.strip()}\n"
        )
    return "\n".join(blocks)


def to_txt(segments: list[SegmentLike]) -> str:
    return "\n".join(s.text.strip() for s in segments) + "\n"


def to_md(segments: list[SegmentLike]) -> str:
    lines = ["# Transcript\n"]
    for s in segments:
        stamp = _clock(s.start_ms, ".")[:-4]  # HH:MM:SS, sin milisegundos
        lines.append(f"**[{stamp}]** {s.text.strip()}\n")
    return "\n".join(lines)


# formato → (función de render, extensión, media-type para la descarga)
FORMATS: dict[str, tuple] = {
    "srt": (to_srt, "srt", "application/x-subrip"),
    "vtt": (to_vtt, "vtt", "text/vtt"),
    "txt": (to_txt, "txt", "text/plain"),
    "md": (to_md, "md", "text/markdown"),
}


def render(fmt: str, segments: list[SegmentLike]) -> tuple[str, str, str]:
    """Devuelve (contenido, extensión, media_type) para `fmt`.

    Lanza KeyError si el formato no está soportado (la ruta lo traduce a 400).
    """
    fn, ext, media = FORMATS[fmt]
    return fn(segments), ext, media
