"""Integración real del pipeline: ffmpeg + faster-whisper sobre un audio fixture.

Es el test end-to-end, sin stubs. Lento (carga el modelo `tiny` y transcribe
~3 s de audio) pero es la única prueba que ejerce el motor de verdad.
Se salta si falta ffmpeg para no romper la suite en máquinas sin él.
"""

import asyncio
import contextlib
import shutil
from pathlib import Path

import pytest

import lscrib.worker.queue as wq
from lscrib.domain.models import JobStatus, MediaType

FIXTURE = Path(__file__).parent / "fixtures" / "sample_en.mp3"

_TERMINAL = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED}

pytestmark = [
    pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg no instalado"),
    pytest.mark.skipif(not FIXTURE.exists(), reason="falta el audio fixture"),
]


def test_real_pipeline_produces_text(worker_env):
    job_id = worker_env.add_job(
        original_filename=FIXTURE.name,
        media_path=str(FIXTURE),
        media_type=MediaType.AUDIO,
        model="tiny",
        status=JobStatus.QUEUED,
    )

    q = wq.JobQueue()

    async def scenario():
        task = asyncio.create_task(q.run_forever())
        await q.enqueue(job_id)
        for _ in range(3000):  # hasta ~60 s de margen
            await asyncio.sleep(0.02)
            job = worker_env.get(job_id)
            if job is not None and job.status in _TERMINAL:
                break
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())

    job = worker_env.get(job_id)
    assert job.status == JobStatus.COMPLETED, f"error: {job.error}"
    assert job.progress == 1.0
    assert job.duration_sec and job.duration_sec >= 2
    assert job.language  # se detectó algún idioma

    segments = worker_env.segments(job_id)
    assert segments, "el pipeline debe producir al menos un segmento"
    text = " ".join(s.text for s in segments).strip()
    assert text, "el transcript no debe estar vacío"

    # timestamps por palabra presentes en al menos un segmento
    assert any(s.words for s in segments)

    # el wav normalizado temporal se limpió; el fixture original sigue intacto
    assert not (worker_env.data_dir / f"{job_id}.wav").exists()
    assert FIXTURE.exists()
