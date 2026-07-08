"""Catálogo de modelos Whisper con su trade-off (R5: decisión informada).

La UI muestra siempre peso, velocidad relativa y calidad esperada antes de
descargar (R2: descarga explícita, se avisa el tamaño).
"""

import os
from pathlib import Path

from pydantic import BaseModel


class ModelInfo(BaseModel):
    name: str
    size_label: str       # peso aproximado de descarga
    speed: str            # velocidad relativa
    quality: str          # calidad esperada
    note: str = ""


class ModelStatus(ModelInfo):
    """ModelInfo + si ya está en caché local (✓) o se bajaría (R2)."""

    downloaded: bool = False


# Tamaños aproximados de los modelos faster-whisper (CTranslate2, int8).
CATALOG: list[ModelInfo] = [
    ModelInfo(name="tiny", size_label="~75 MB", speed="muy rápida", quality="básica",
              note="ideal para probar o audio limpio y corto"),
    ModelInfo(name="base", size_label="~145 MB", speed="rápida", quality="aceptable"),
    ModelInfo(name="small", size_label="~480 MB", speed="media", quality="buena",
              note="buen equilibrio por defecto"),
    ModelInfo(name="medium", size_label="~1.5 GB", speed="lenta", quality="muy buena"),
    ModelInfo(name="large-v3", size_label="~3 GB", speed="muy lenta", quality="máxima",
              note="la mejor precisión; pide RAM y paciencia (R5)"),
]

CATALOG_BY_NAME = {m.name: m for m in CATALOG}

# faster-whisper baja los pesos de estos repos de Hugging Face y los cachea en
# `<hub>/models--<org>--faster-whisper-<name>`. Detectamos ambos (Systran es el
# actual; guillaumekln, el histórico) para marcar "descargado ✓" (R2/R5).
_HF_ORGS = ("Systran", "guillaumekln")


def _hub_cache_dir() -> Path:
    """Carpeta `hub` de la caché de Hugging Face, respetando las env vars."""
    if (hub := os.getenv("HF_HUB_CACHE")) or (hub := os.getenv("HUGGINGFACE_HUB_CACHE")):
        return Path(hub)
    home = os.getenv("HF_HOME")
    base = Path(home) if home else Path.home() / ".cache" / "huggingface"
    return base / "hub"


def is_downloaded(name: str) -> bool:
    """True si el modelo ya está en caché local (best-effort, no toca la red)."""
    hub = _hub_cache_dir()
    for org in _HF_ORGS:
        repo = hub / f"models--{org}--faster-whisper-{name}"
        snapshots = repo / "snapshots"
        # un snapshot con contenido = descarga completada
        if snapshots.is_dir() and any(p.is_dir() for p in snapshots.iterdir()):
            return True
    return False


def catalog_with_status() -> list[ModelStatus]:
    """Catálogo enriquecido con el flag `downloaded` para la UI (R5)."""
    return [
        ModelStatus(**m.model_dump(), downloaded=is_downloaded(m.name)) for m in CATALOG
    ]
