"""Endpoints de metadatos: catálogo de modelos para el selector de la UI (R5)."""

from fastapi import APIRouter
from pydantic import BaseModel

from lscrib.config import settings
from lscrib.models.registry import ModelStatus, catalog_with_status

router = APIRouter(prefix="/api", tags=["meta"])


class ModelsResponse(BaseModel):
    default: str  # modelo preseleccionado en la UI (doc 08: `small`)
    models: list[ModelStatus]


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """Catálogo Whisper con trade-offs y si ya está descargado (R2/R5)."""
    return ModelsResponse(default=settings.default_model, models=catalog_with_status())
