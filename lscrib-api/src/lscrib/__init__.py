"""lscrib — API local-first de transcripción con Whisper.

El audio nunca sale de la máquina (R1). Este paquete expone una API FastAPI
y un worker en proceso que normaliza (ffmpeg) y transcribe (faster-whisper).
"""

__version__ = "0.1.0"


def main() -> None:
    """Punto de entrada `uv run lscrib` (R13: un comando)."""
    import uvicorn

    from lscrib.config import settings

    uvicorn.run(
        "lscrib.api.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=False,
    )
