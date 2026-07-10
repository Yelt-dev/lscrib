"""Endpoints de metadatos: catálogo de modelos para el selector de la UI."""

from fastapi import APIRouter
from pydantic import BaseModel

from lscrib.config import settings
from lscrib.models.registry import ModelStatus, catalog_with_status

router = APIRouter(prefix="/api", tags=["meta"])


class ModelsResponse(BaseModel):
    default: str  # modelo preseleccionado en la UI
    models: list[ModelStatus]


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """Catálogo Whisper con trade-offs y si el modelo ya está descargado."""
    return ModelsResponse(default=settings.default_model, models=catalog_with_status())
