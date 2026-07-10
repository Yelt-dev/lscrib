"""Bus de eventos en memoria: el worker publica progreso, el SSE lo consume.

Un job puede tener varios suscriptores (varias pestañas abiertas). El worker
llama `publish(job_id, evento)` en cada cambio; cada ruta SSE `subscribe()` y
recibe los eventos por su propia cola (progreso server→cliente).
"""

import asyncio
from collections import defaultdict


class JobEvent:
    """Evento emitido por el worker hacia los clientes SSE."""

    __slots__ = ("status", "progress", "language", "error", "done")

    def __init__(
        self,
        status: str,
        progress: float = 0.0,
        language: str | None = None,
        error: str | None = None,
        done: bool = False,
    ) -> None:
        self.status = status
        self.progress = progress
        self.language = language
        self.error = error
        self.done = done  # último evento → el SSE cierra la conexión

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "progress": round(self.progress, 4),
            "language": self.language,
            "error": self.error,
        }


class EventBroker:
    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue]] = defaultdict(set)

    def subscribe(self, job_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subs[job_id].add(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        subs = self._subs.get(job_id)
        if subs is not None:
            subs.discard(q)
            if not subs:
                del self._subs[job_id]

    def publish(self, job_id: str, event: JobEvent) -> None:
        """No bloquea: encola en cada suscriptor. Sin suscriptores, es un no-op."""
        for q in list(self._subs.get(job_id, ())):
            q.put_nowait(event)


broker = EventBroker()
