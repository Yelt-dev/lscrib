"""Worker en proceso: procesa la cola secuencialmente, emite progreso (SSE).

Sin Redis/Celery: la simplicidad de operación es una feature.
El pipeline por trabajo es: normalizing (ffmpeg) → transcribing (whisper) →
completed, persistiendo Segment y publicando progreso en cada paso.
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from lscrib.config import settings
from lscrib.db.models import Job, Segment
from lscrib.db.session import engine
from lscrib.domain.models import JobStatus, can_transition
from lscrib.media.ffmpeg import normalize, probe_duration
from lscrib.transcribe.whisper import transcribe
from lscrib.worker.events import JobEvent, broker


class JobCanceled(Exception):
    """El usuario canceló el trabajo en curso."""


def _next(iterator):
    """`next()` sin StopIteration, para poder correrlo en un hilo con to_thread."""
    try:
        return next(iterator)
    except StopIteration:
        return None


class JobQueue:
    """Un único trabajo activo a la vez. El orden lo da `Job.position` en la
    BD (reordenable), no una cola en memoria: el worker despierta por un evento y
    elige el siguiente `queued` con menor posición."""

    def __init__(self) -> None:
        self._wakeup = asyncio.Event()
        self._current: str | None = None
        self._cancel: set[str] = set()
        self._task: asyncio.Task | None = None

    # --- API pública ---------------------------------------------------------

    async def enqueue(self, job_id: str) -> None:
        """Señala que hay trabajo nuevo (la posición ya la fijó la ruta)."""
        self._wakeup.set()

    def notify(self) -> None:
        self._wakeup.set()

    def request_cancel(self, job_id: str) -> None:
        """Marca un trabajo en curso para cancelar. El worker converge."""
        self._cancel.add(job_id)

    @property
    def current(self) -> str | None:
        return self._current

    def start(self) -> None:
        """Arranca el bucle del worker (llamado desde el lifespan de la app)."""
        if self._task is None:
            self._task = asyncio.create_task(self.run_forever())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    # --- bucle interno -------------------------------------------------------

    def _next_queued_id(self) -> str | None:
        with Session(engine) as session:
            job = session.exec(
                select(Job)
                .where(Job.status == JobStatus.QUEUED)
                .order_by(Job.position, Job.created_at)
            ).first()
            return job.id if job else None

    async def run_forever(self) -> None:
        while True:
            job_id = self._next_queued_id()
            if job_id is None:
                # Nada pendiente: espera un evento. Doble chequeo evita la carrera
                # entre "no hay" y "clear" (un enqueue justo en medio).
                self._wakeup.clear()
                job_id = self._next_queued_id()
                if job_id is None:
                    await self._wakeup.wait()
                    continue
            self._current = job_id
            try:
                await self._process(job_id)
            except JobCanceled:
                self._finish(job_id, JobStatus.CANCELED)
            except Exception as exc:  # noqa: BLE001 — degradar con claridad
                self._finish(job_id, JobStatus.FAILED, error=str(exc))
            finally:
                self._cancel.discard(job_id)
                self._current = None

    def _raise_if_canceled(self, job_id: str) -> None:
        if job_id in self._cancel:
            raise JobCanceled

    def _advance(
        self, session: Session, job: Job, new_status: JobStatus, progress: float
    ) -> None:
        """Valida la transición, persiste y publica el evento SSE."""
        if not can_transition(job.status, new_status):
            raise RuntimeError(
                f"transición inválida {job.status} → {new_status} (job {job.id})"
            )
        job.status = new_status
        job.progress = progress
        session.add(job)
        session.commit()
        broker.publish(job.id, JobEvent(new_status.value, progress, language=job.language))

    async def _process(self, job_id: str) -> None:
        """uploaded → normalizing (ffmpeg) → transcribing (whisper) → completed."""
        wav_path = settings.data_dir / f"{job_id}.wav"
        with Session(engine) as session:
            job = session.get(Job, job_id)
            if job is None or job.status != JobStatus.QUEUED:
                # Cancelado mientras esperaba turno, o ya procesado: nada que hacer.
                return

            # 1) Normalización (ffmpeg): cualquier formato → wav 16 kHz mono.
            self._advance(session, job, JobStatus.NORMALIZING, progress=0.0)
            src = Path(job.media_path)
            duration = await probe_duration(src)
            job.duration_sec = duration
            session.add(job)
            session.commit()
            await normalize(src, wav_path)
            self._raise_if_canceled(job_id)

            # 2) Transcripción (faster-whisper). Cargar modelo + detectar idioma
            #    es bloqueante → hilo aparte para no congelar el event loop.
            self._advance(session, job, JobStatus.TRANSCRIBING, progress=0.0)
            forced = None if job.language in (None, "auto") else job.language
            tr = await asyncio.to_thread(
                transcribe, wav_path, job.model, forced, job.prompt
            )
            total = float(duration or tr.duration_sec or 0.0)
            job.language = tr.language  # idioma detectado
            session.add(job)
            session.commit()
            broker.publish(
                job_id,
                JobEvent(JobStatus.TRANSCRIBING.value, 0.0, language=tr.language),
            )

            # 3) Persistir cada segmento a medida que llega + progreso en vivo.
            iterator = tr.segments
            while True:
                seg = await asyncio.to_thread(_next, iterator)
                if seg is None:
                    break
                self._raise_if_canceled(job_id)
                session.add(
                    Segment(
                        job_id=job_id,
                        index=seg.index,
                        start_ms=seg.start_ms,
                        end_ms=seg.end_ms,
                        text=seg.text,
                        words=seg.words,
                    )
                )
                progress = min((seg.end_ms / 1000.0) / total, 0.999) if total else 0.0
                job.progress = progress
                session.add(job)
                session.commit()
                broker.publish(
                    job_id,
                    JobEvent(JobStatus.TRANSCRIBING.value, progress, language=job.language),
                )

            # 4) Completado.
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
            job.completed_at = datetime.now(UTC)
            session.add(job)
            session.commit()
            broker.publish(
                job_id,
                JobEvent(JobStatus.COMPLETED.value, 1.0, language=job.language, done=True),
            )

        # Éxito: el wav normalizado ya no hace falta.
        wav_path.unlink(missing_ok=True)

    def _finish(
        self, job_id: str, status: JobStatus, error: str | None = None
    ) -> None:
        """Marca un desenlace no-feliz (failed/canceled), limpia temporales."""
        (settings.data_dir / f"{job_id}.wav").unlink(missing_ok=True)
        with Session(engine) as session:
            job = session.get(Job, job_id)
            if job is None:
                return
            job.status = status
            job.error = error
            session.add(job)
            session.commit()
            broker.publish(
                job_id,
                JobEvent(status.value, job.progress, error=error, done=True),
            )


queue = JobQueue()
