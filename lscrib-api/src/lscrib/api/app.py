"""Fábrica de la app FastAPI. Sirve la API + SSE de progreso (doc 06)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from lscrib import __version__
from lscrib.api.meta import router as meta_router
from lscrib.api.routes import router as jobs_router
from lscrib.config import settings
from lscrib.db.session import init_db, recover_stuck_jobs
from lscrib.worker.queue import queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Un reinicio deja trabajos a medias: se marcan failed para no mentir (R14).
    recover_stuck_jobs()
    queue.start()  # worker en proceso, un job a la vez (R7)
    try:
        yield
    finally:
        await queue.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="lscrib", version=__version__, lifespan=lifespan)

    # En dev el front (Vite, :5173) llama a la API (:8000). En prod FastAPI
    # sirve el build estático y esto sobra.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    app.include_router(jobs_router)
    app.include_router(meta_router)

    # En producción (un comando, R13) el backend sirve el build de React desde el
    # mismo origen. Se monta al final: /health y /api/* ya están registrados y
    # tienen prioridad; el resto cae al SPA. En dev static_dir=None y esto se salta.
    if settings.static_dir and settings.static_dir.is_dir():
        app.mount(
            "/", StaticFiles(directory=settings.static_dir, html=True), name="spa"
        )

    return app
