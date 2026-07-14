"""Endpoints de metadatos: catálogo de modelos y capacidades de la máquina."""

from fastapi import APIRouter
from pydantic import BaseModel

from lscrib import __version__
from lscrib.config import settings
from lscrib.models.registry import ModelStatus, catalog_with_status
from lscrib.system.cpu import check_cpu

router = APIRouter(prefix="/api", tags=["meta"])


class ModelsResponse(BaseModel):
    default: str  # modelo preseleccionado en la UI
    models: list[ModelStatus]


class CpuInfo(BaseModel):
    supported: bool
    cpu_model: str
    missing: list[str]
    message: str  # vacío si `supported`; si no, qué pasa y por qué


class SystemResponse(BaseModel):
    version: str
    cpu: CpuInfo


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """Catálogo Whisper con trade-offs y si el modelo ya está descargado."""
    return ModelsResponse(default=settings.default_model, models=catalog_with_status())


@router.get("/system", response_model=SystemResponse)
async def system_info() -> SystemResponse:
    """Capacidades del anfitrión. La UI lo consulta al cargar para avisar antes
    de que el usuario suba un archivo que nunca se va a poder transcribir."""
    support = check_cpu()
    return SystemResponse(
        version=__version__,
        cpu=CpuInfo(
            supported=support.supported,
            cpu_model=support.cpu_model,
            missing=support.missing,
            message=support.message(),
        ),
    )
