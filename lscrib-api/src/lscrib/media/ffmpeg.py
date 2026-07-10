"""Wrapper de ffmpeg: cualquier formato → wav 16 kHz mono.

El usuario no debe preocuparse del formato. Si falta ffmpeg, mensaje claro de
cómo instalarlo, no un stack trace.
"""

import asyncio
import shutil
from pathlib import Path


class FfmpegNotFound(RuntimeError):
    """ffmpeg no está en el PATH. Mensaje amable para el usuario."""

    def __init__(self) -> None:
        super().__init__(
            "ffmpeg no encontrado. Instálalo: macOS `brew install ffmpeg`, "
            "Debian/Ubuntu `apt install ffmpeg`."
        )


class FfmpegError(RuntimeError):
    """ffmpeg/ffprobe corrió pero falló. Guarda stderr para diagnóstico."""


def ensure_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if path is None:
        raise FfmpegNotFound
    return path


def _ensure_ffprobe() -> str:
    path = shutil.which("ffprobe")
    if path is None:
        raise FfmpegNotFound
    return path


async def _run(program: str, *args: str) -> tuple[bytes, bytes]:
    """Ejecuta un binario y devuelve (stdout, stderr). Lanza FfmpegError si falla."""
    proc = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        detail = stderr.decode("utf-8", "replace").strip().splitlines()
        tail = detail[-1] if detail else f"código {proc.returncode}"
        raise FfmpegError(f"{Path(program).name} falló: {tail}")
    return stdout, stderr


async def normalize(src: Path, dst: Path) -> None:
    """Convierte `src` (cualquier formato) a wav 16 kHz mono en `dst`.

    16 kHz mono PCM es lo que espera Whisper. `-vn` descarta cualquier
    pista de video: de un mp4 solo nos interesa el audio.
    """
    ffmpeg = ensure_ffmpeg()
    dst.parent.mkdir(parents=True, exist_ok=True)
    await _run(
        ffmpeg,
        "-nostdin",
        "-y",
        "-i",
        str(src),
        "-vn",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(dst),
    )


async def probe_duration(src: Path) -> int:
    """Duración en segundos vía ffprobe (para Job.duration_sec y el % de progreso).

    Devuelve el entero de segundos (redondeado hacia arriba). Si ffprobe no
    reporta duración, devuelve 0 (el progreso caerá a indeterminado, no rompe).
    """
    ffprobe = _ensure_ffprobe()
    stdout, _ = await _run(
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(src),
    )
    raw = stdout.decode("utf-8", "replace").strip()
    try:
        seconds = float(raw)
    except ValueError:
        return 0
    return max(0, int(seconds + 0.999))
