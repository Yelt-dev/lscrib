"""¿Puede esta CPU ejecutar el motor de transcripción?

NumPy y CTranslate2 (el motor bajo faster-whisper) publican ruedas x86-64 que
asumen **x86-64-v2**: SSE4.2 como mínimo. En un procesador anterior (p. ej. un
AMD K10 de 2010, que solo tiene SSE4a) el proceso muere con SIGILL —instrucción
ilegal— *al importar NumPy*, antes de llegar a nuestro código. El backend
desaparece sin traza, el contenedor reinicia y el usuario no ve más que
peticiones cortadas.

Detectarlo aquí convierte esa muerte muda en un mensaje que explica qué pasa.
"""

import os
import platform
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

_CPUINFO = Path("/proc/cpuinfo")

# Arquitecturas donde aplica el chequeo. En arm64 (Apple Silicon, Raspberry) las
# ruedas traen NEON y no hay baseline que fallar: no hay nada que comprobar.
_X86 = frozenset({"x86_64", "amd64", "i386", "i686", "x86"})

# Baseline x86-64-v2. SSE4.2 es el que piden CTranslate2 y las ruedas de NumPy;
# los demás flags de v2 vienen de la mano en cualquier CPU que tenga SSE4.2, así
# que con este basta para decidir y el mensaje queda claro.
_REQUIRED = ("sse4_2",)


class UnsupportedCpu(RuntimeError):
    """La CPU no tiene las instrucciones que exige el motor de transcripción."""


@dataclass(frozen=True)
class CpuSupport:
    """Veredicto sobre la CPU actual. `missing` está vacío si `supported`."""

    supported: bool
    cpu_model: str = ""
    missing: list[str] = field(default_factory=list)

    def message(self) -> str:
        """Explicación para el usuario. Vacía si la CPU sirve."""
        if self.supported:
            return ""
        who = self.cpu_model or "El procesador de este equipo"
        flags = ", ".join(f.upper().replace("_", ".") for f in self.missing)
        return (
            f"{who} no soporta {flags}. faster-whisper (CTranslate2) y NumPy "
            "necesitan esas instrucciones, así que lscrib no puede transcribir "
            "en esta máquina."
        )


def _parse_cpuinfo(text: str) -> tuple[set[str], str]:
    """Extrae (flags, modelo) de un /proc/cpuinfo. Solo mira el primer núcleo."""
    flags: set[str] = set()
    model = ""
    for line in text.splitlines():
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "flags" and not flags:
            flags = set(value.split())
        elif key == "model name" and not model:
            model = re.sub(r"\s+", " ", value)
        if flags and model:
            break
    return flags, model


def _read_cpuinfo() -> str | None:
    """Contenido de /proc/cpuinfo, o None si no se puede leer (macOS, Windows…)."""
    try:
        return _CPUINFO.read_text()
    except OSError:
        return None


@lru_cache(maxsize=1)
def check_cpu() -> CpuSupport:
    """Veredicto sobre la CPU. Ante la duda, dice que sí: no llorar en falso.

    Solo se pronuncia cuando puede leer los flags de verdad (x86 con
    `/proc/cpuinfo`, es decir Linux). En macOS o arm no hay nada que comprobar,
    y en un entorno donde no se puedan leer los flags preferimos dejar pasar
    antes que bloquear una máquina perfectamente capaz.
    """
    if os.getenv("LSCRIB_IGNORE_CPU_CHECK"):
        return CpuSupport(supported=True)
    if platform.machine().lower() not in _X86:
        return CpuSupport(supported=True)

    text = _read_cpuinfo()
    if text is None:
        return CpuSupport(supported=True)

    flags, model = _parse_cpuinfo(text)
    if not flags:
        return CpuSupport(supported=True, cpu_model=model)

    missing = [f for f in _REQUIRED if f not in flags]
    return CpuSupport(supported=not missing, cpu_model=model, missing=missing)


def ensure_cpu_supported() -> None:
    """Lanza `UnsupportedCpu` antes de importar NumPy/CTranslate2 y morir con SIGILL."""
    support = check_cpu()
    if not support.supported:
        raise UnsupportedCpu(support.message())
