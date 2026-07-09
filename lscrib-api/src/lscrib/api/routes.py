"""Rutas de Jobs: subida, cola, cancelación, progreso (SSE) y export (doc 07/08)."""

import asyncio
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select
from sse_starlette.sse import EventSourceResponse

from lscrib.config import settings
from lscrib.db.models import Job, Segment
from lscrib.db.session import get_session
from lscrib.domain.models import (
    JobDetail,
    JobRead,
    JobStatus,
    MediaType,
    SegmentRead,
    can_transition,
)
from lscrib.models.registry import CATALOG_BY_NAME
from lscrib.worker.events import JobEvent, broker
from lscrib.worker.queue import queue

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

_VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mpg", ".mpeg"}
_TERMINAL = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED}
_CANCELABLE = {JobStatus.QUEUED, JobStatus.NORMALIZING, JobStatus.TRANSCRIBING}
_CHUNK = 1 << 20  # 1 MiB


def _media_type(filename: str, content_type: str | None) -> MediaType:
    if Path(filename).suffix.lower() in _VIDEO_EXTS:
        return MediaType.VIDEO
    if content_type and content_type.startswith("video/"):
        return MediaType.VIDEO
    return MediaType.AUDIO


def _to_read(job: Job) -> JobRead:
    return JobRead.model_validate(job, from_attributes=True)


def _get_or_404(session: Session, job_id: str) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return job


def _next_position(session: Session) -> int:
    """Siguiente posición al final de la cola (R7). Los `queued` mantienen orden."""
    positions = session.exec(
        select(Job.position).where(Job.status == JobStatus.QUEUED)
    ).all()
    return (max(positions) + 1) if positions else 1


@router.post("", response_model=JobRead)
async def create_job(
    response: Response,
    file: UploadFile,
    model: str = Form(default=""),
    language: str = Form(default="auto"),
    session: Session = Depends(get_session),
):
    """Subida por arrastre → calcula hash, guarda, estado `uploaded` (R6/R9/R15)."""
    model = model or settings.default_model
    if model not in CATALOG_BY_NAME:
        raise HTTPException(status_code=400, detail=f"Modelo desconocido: {model}")

    job_id = str(uuid4())
    suffix = Path(file.filename or "").suffix
    dest = settings.data_dir / f"{job_id}{suffix}"
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Stream a disco calculando SHA-256 (R9) sin cargar el archivo en RAM (R15).
    max_bytes = settings.max_file_mb * 1024 * 1024
    hasher = hashlib.sha256()
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(_CHUNK):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Archivo supera el límite de {settings.max_file_mb} MB",
                    )
                hasher.update(chunk)
                out.write(chunk)
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise

    if size == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Archivo vacío")

    file_hash = hasher.hexdigest()

    # Idempotencia (R9): si ya existe un trabajo con este hash, reusarlo.
    existing = session.exec(
        select(Job).where(Job.file_hash == file_hash)
    ).first()
    if existing is not None:
        dest.unlink(missing_ok=True)
        response.headers["X-Existing-Job"] = "true"
        return _to_read(existing)

    job = Job(
        id=job_id,
        original_filename=file.filename or f"{job_id}{suffix}",
        file_hash=file_hash,
        media_path=str(dest),
        media_type=_media_type(file.filename or "", file.content_type),
        language=None if language == "auto" else language,
        model=model,
        status=JobStatus.UPLOADED,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return _to_read(job)


@router.get("", response_model=list[JobRead])
async def list_jobs(session: Session = Depends(get_session)):
    """Lista de trabajos, más recientes primero (para la cola batch del MVP)."""
    jobs = session.exec(select(Job).order_by(Job.created_at.desc())).all()
    return [_to_read(j) for j in jobs]


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: str, session: Session = Depends(get_session)):
    job = _get_or_404(session, job_id)
    segments = session.exec(
        select(Segment).where(Segment.job_id == job_id).order_by(Segment.index)
    ).all()
    detail = JobDetail.model_validate(job, from_attributes=True)
    detail.segments = [SegmentRead.model_validate(s, from_attributes=True) for s in segments]
    return detail


class SegmentUpdate(BaseModel):
    text: str


@router.patch("/{job_id}/segments/{index}", response_model=SegmentRead)
async def update_segment(
    job_id: str,
    index: int,
    body: SegmentUpdate,
    session: Session = Depends(get_session),
):
    """Edición del transcript por segmento (doc 09). Los exports reflejan el cambio."""
    seg = session.exec(
        select(Segment).where(Segment.job_id == job_id, Segment.index == index)
    ).first()
    if seg is None:
        raise HTTPException(status_code=404, detail="Segmento no encontrado")
    seg.text = body.text
    session.add(seg)
    session.commit()
    session.refresh(seg)
    return SegmentRead.model_validate(seg, from_attributes=True)


@router.post("/{job_id}/transcribe", response_model=JobRead)
async def start_transcription(
    job_id: str,
    model: str | None = Query(default=None),
    language: str | None = Query(default=None),
    prompt: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    """`uploaded → queued` (acción explícita, doc 07). También reintenta failed/canceled.

    `model`/`language`/`prompt` opcionales permiten reprocesar con otra elección
    (doc 07). `prompt` es vocabulario (nombres propios, jerga) para acertar mejor.
    """
    job = _get_or_404(session, job_id)
    if not can_transition(job.status, JobStatus.QUEUED):
        raise HTTPException(
            status_code=409,
            detail=f"No se puede encolar desde estado '{job.status.value}'",
        )
    if model is not None:
        if model not in CATALOG_BY_NAME:
            raise HTTPException(status_code=400, detail=f"Modelo desconocido: {model}")
        job.model = model
    if language is not None:
        job.language = None if language == "auto" else language
    if prompt is not None:
        job.prompt = prompt.strip() or None
    # Reintento: descarta segmentos parciales de una pasada anterior.
    for seg in session.exec(select(Segment).where(Segment.job_id == job_id)).all():
        session.delete(seg)
    job.status = JobStatus.QUEUED
    job.progress = 0.0
    job.error = None
    job.position = _next_position(session)  # al final de la cola (R7)
    session.add(job)
    session.commit()
    session.refresh(job)

    await queue.enqueue(job_id)
    broker.publish(job_id, JobEvent(JobStatus.QUEUED.value, 0.0, language=job.language))
    return _to_read(job)


@router.post("/{job_id}/cancel", response_model=JobRead)
async def cancel_job(job_id: str, session: Session = Depends(get_session)):
    """Cancela en queued/normalizing/transcribing (R8)."""
    job = _get_or_404(session, job_id)
    if job.status not in _CANCELABLE:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede cancelar en estado '{job.status.value}'",
        )

    if job.status == JobStatus.QUEUED:
        # Aún no lo toca el worker: lo cancelamos aquí; al desencolar lo saltará.
        job.status = JobStatus.CANCELED
        session.add(job)
        session.commit()
        session.refresh(job)
        broker.publish(
            job_id, JobEvent(JobStatus.CANCELED.value, job.progress, done=True)
        )
    else:
        # En curso: se lo pedimos al worker, que converge a canceled y limpia (R8).
        queue.request_cancel(job_id)

    return _to_read(job)


@router.post("/{job_id}/move", response_model=list[JobRead])
async def move_job(
    job_id: str,
    direction: str = Query(...),
    session: Session = Depends(get_session),
):
    """Reordena un trabajo `queued` en la cola (R7). direction = up | down."""
    if direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="direction debe ser 'up' o 'down'")
    job = _get_or_404(session, job_id)
    if job.status != JobStatus.QUEUED:
        raise HTTPException(status_code=409, detail="Solo se reordenan trabajos en cola")

    queued = session.exec(
        select(Job).where(Job.status == JobStatus.QUEUED).order_by(Job.position, Job.created_at)
    ).all()
    ids = [j.id for j in queued]
    i = ids.index(job_id)
    swap = i - 1 if direction == "up" else i + 1
    if 0 <= swap < len(queued):
        a, b = queued[i], queued[swap]
        a.position, b.position = b.position, a.position
        session.add(a)
        session.add(b)
        session.commit()

    jobs = session.exec(select(Job).order_by(Job.created_at.desc())).all()
    return [_to_read(j) for j in jobs]


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, session: Session = Depends(get_session)):
    """Borrado real (R3): elimina el trabajo, sus segmentos y los archivos de disco.

    No borra el trabajo que el worker está procesando ahora; primero hay que
    cancelarlo (evita borrar archivos en uso).
    """
    job = _get_or_404(session, job_id)
    if queue.current == job_id:
        raise HTTPException(
            status_code=409, detail="Cancela el trabajo en curso antes de borrarlo"
        )

    for seg in session.exec(select(Segment).where(Segment.job_id == job_id)).all():
        session.delete(seg)
    # Sin papelera oculta (R3): fuera el original y el wav temporal.
    for path in (Path(job.media_path), settings.data_dir / f"{job_id}.wav"):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    session.delete(job)
    session.commit()
    return Response(status_code=204)


@router.get("/{job_id}/events")
async def job_events(job_id: str, request: Request):
    """SSE: progreso server→cliente en vivo (doc 06). El corazón de la UX."""
    with next(get_session()) as session:
        job = session.get(Job, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Trabajo no encontrado")
        initial = JobEvent(
            job.status.value, job.progress, language=job.language, error=job.error,
            done=job.status in _TERMINAL,
        )

    q = broker.subscribe(job_id)

    async def event_stream():
        try:
            yield {"data": json.dumps(initial.as_dict())}
            if initial.done:
                return
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event: JobEvent = await asyncio.wait_for(q.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}  # mantiene viva la conexión
                    continue
                yield {"data": json.dumps(event.as_dict())}
                if event.done:
                    break
        finally:
            broker.unsubscribe(job_id, q)

    return EventSourceResponse(event_stream())


@router.get("/{job_id}/media")
async def get_media(job_id: str, session: Session = Depends(get_session)):
    """Sirve el archivo original para el reproductor sincronizado (doc 09).

    Local-first (R1): el archivo nunca sale de la máquina; esto lo entrega al
    navegador del propio usuario en localhost.
    """
    job = _get_or_404(session, job_id)
    path = Path(job.media_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="El archivo ya no está en disco")
    return FileResponse(
        path,
        filename=job.original_filename,
        headers={"Accept-Ranges": "bytes"},  # permite seek en <audio>/<video>
    )


@router.get("/{job_id}/export")
async def export_transcript(
    job_id: str,
    format: str = Query(default="srt"),
    session: Session = Depends(get_session),
):
    """Exporta a srt | vtt | txt | md. Determinista (R12)."""
    from lscrib.export import render

    job = _get_or_404(session, job_id)
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="El transcript aún no está listo")

    segments = session.exec(
        select(Segment).where(Segment.job_id == job_id).order_by(Segment.index)
    ).all()
    try:
        content, ext, media = render(format, list(segments))
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Formato no soportado: {format}")

    stem = Path(job.original_filename).stem or job_id
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{stem}.{ext}"'},
    )
