"""Tests del worker con stubs de ffmpeg/whisper: rápidos, deterministas, portables.

Cubren el pipeline y los desenlaces (completed/canceled/failed) sin correr Whisper.
"""

import asyncio
import contextlib

import lscrib.worker.queue as wq
from lscrib.domain.models import JobStatus
from lscrib.transcribe.whisper import TranscribedSegment, Transcription
from lscrib.worker.events import broker

_TERMINAL = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED}


def _stub_media(monkeypatch):
    """normalize crea el wav; probe_duration devuelve 10 s."""

    async def fake_normalize(src, dst):
        dst.write_bytes(b"fake wav")

    async def fake_probe(src):
        return 10

    monkeypatch.setattr(wq, "normalize", fake_normalize)
    monkeypatch.setattr(wq, "probe_duration", fake_probe)


def _run_job(env, job_id: str) -> list:
    """Corre run_forever hasta que el job llega a un estado terminal.

    Devuelve los eventos SSE publicados para ese job.
    """
    q = wq.JobQueue()
    events: list = []

    async def scenario():
        sub = broker.subscribe(job_id)
        task = asyncio.create_task(q.run_forever())
        await q.enqueue(job_id)
        for _ in range(500):
            await asyncio.sleep(0.01)
            job = env.get(job_id)
            if job is not None and job.status in _TERMINAL:
                break
        await asyncio.sleep(0.02)  # deja drenar el último evento
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        while not sub.empty():
            events.append(sub.get_nowait())
        broker.unsubscribe(job_id, sub)

    asyncio.run(scenario())
    return events


def test_happy_path_completes_and_persists(worker_env, monkeypatch):
    _stub_media(monkeypatch)

    def fake_transcribe(path, model, language, prompt=None):
        def gen():
            yield TranscribedSegment(0, 0, 5000, "hola")
            yield TranscribedSegment(1, 5000, 10000, "mundo")

        return Transcription(language="es", duration_sec=10.0, segments=gen())

    monkeypatch.setattr(wq, "transcribe", fake_transcribe)

    job_id = worker_env.add_job()
    events = _run_job(worker_env, job_id)

    job = worker_env.get(job_id)
    assert job.status == JobStatus.COMPLETED
    assert job.progress == 1.0
    assert job.language == "es"  # idioma detectado
    assert job.completed_at is not None

    texts = [s.text for s in worker_env.segments(job_id)]
    assert texts == ["hola", "mundo"]

    statuses = [e.status for e in events]
    assert statuses[0] == "normalizing"
    assert "transcribing" in statuses
    assert statuses[-1] == "completed"
    assert events[-1].done is True

    # el wav temporal se limpia al completar
    assert not (worker_env.data_dir / f"{job_id}.wav").exists()


def test_progress_increases_monotonically(worker_env, monkeypatch):
    _stub_media(monkeypatch)

    def fake_transcribe(path, model, language, prompt=None):
        def gen():
            for i in range(1, 6):
                yield TranscribedSegment(i - 1, (i - 1) * 2000, i * 2000, f"s{i}")

        return Transcription(language="en", duration_sec=10.0, segments=gen())

    monkeypatch.setattr(wq, "transcribe", fake_transcribe)

    job_id = worker_env.add_job()
    events = _run_job(worker_env, job_id)

    progresses = [e.progress for e in events if e.status == "transcribing" and e.progress > 0]
    assert progresses == sorted(progresses)
    assert all(p <= 1.0 for p in progresses)


def test_cancel_midway_cleans_up(worker_env, monkeypatch):
    _stub_media(monkeypatch)

    def make_transcribe(q):
        def fake_transcribe(path, model, language, prompt=None):
            def gen():
                for i in range(5):
                    if i == 1:
                        q.request_cancel(gen.job_id)  # cancelar en curso
                    yield TranscribedSegment(i, i * 1000, (i + 1) * 1000, f"s{i}")

            gen.job_id = fake_transcribe.job_id
            return Transcription(language="en", duration_sec=10.0, segments=gen())

        return fake_transcribe

    job_id = worker_env.add_job()

    # Instanciamos la cola aquí para pasársela al stub (necesita request_cancel).
    q = wq.JobQueue()
    stub = make_transcribe(q)
    stub.job_id = job_id
    monkeypatch.setattr(wq, "transcribe", stub)

    async def scenario():
        task = asyncio.create_task(q.run_forever())
        await q.enqueue(job_id)
        for _ in range(500):
            await asyncio.sleep(0.01)
            job = worker_env.get(job_id)
            if job is not None and job.status in _TERMINAL:
                break
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())

    job = worker_env.get(job_id)
    assert job.status == JobStatus.CANCELED
    assert job.error is None
    # se persistió solo el segmento previo a la cancelación
    assert len(worker_env.segments(job_id)) == 1
    # temporales limpiados
    assert not (worker_env.data_dir / f"{job_id}.wav").exists()


def test_failure_marks_failed_with_message(worker_env, monkeypatch):
    async def boom_normalize(src, dst):
        raise RuntimeError("ffmpeg reventó")

    async def fake_probe(src):
        return 10

    monkeypatch.setattr(wq, "normalize", boom_normalize)
    monkeypatch.setattr(wq, "probe_duration", fake_probe)

    job_id = worker_env.add_job()
    events = _run_job(worker_env, job_id)

    job = worker_env.get(job_id)
    assert job.status == JobStatus.FAILED  # degradar con claridad
    assert "ffmpeg reventó" in (job.error or "")
    assert events[-1].done is True
    assert not (worker_env.data_dir / f"{job_id}.wav").exists()


def test_canceled_while_queued_is_skipped(worker_env, monkeypatch):
    """Si el job ya no está en QUEUED al desencolar, el worker no lo procesa."""
    _stub_media(monkeypatch)
    called = {"transcribe": False}

    def fake_transcribe(path, model, language, prompt=None):
        called["transcribe"] = True
        return Transcription("en", 10.0, iter(()))

    monkeypatch.setattr(wq, "transcribe", fake_transcribe)

    # Job que llega al worker ya en CANCELED (cancelado en cola desde la ruta).
    job_id = worker_env.add_job(status=JobStatus.CANCELED)
    _run_job(worker_env, job_id)

    assert called["transcribe"] is False
    assert worker_env.get(job_id).status == JobStatus.CANCELED
