"""Tests de borrado y reordenado de cola llamando a las rutas directo."""

import asyncio

from sqlmodel import Session, select

from lscrib.api.routes import delete_job, move_job
from lscrib.db.models import Job, Segment
from lscrib.domain.models import JobStatus


def test_delete_removes_files_and_rows(worker_env):
    media = worker_env.data_dir / "orig.mp3"
    media.write_bytes(b"audio")
    wav = worker_env.data_dir / "leftover.wav"  # no debe existir; solo probamos original
    job_id = worker_env.add_job(media_path=str(media), status=JobStatus.COMPLETED)
    with Session(worker_env.engine) as s:
        s.add(Segment(job_id=job_id, index=0, start_ms=0, end_ms=1000, text="hi"))
        s.commit()

    with Session(worker_env.engine) as s:
        asyncio.run(delete_job(job_id, session=s))

    assert not media.exists()  # borrado real de disco
    assert not wav.exists()
    with Session(worker_env.engine) as s:
        assert s.get(Job, job_id) is None
        assert (
            s.exec(select(Segment).where(Segment.job_id == job_id)).all() == []
        )


def test_move_reorders_queue(worker_env):
    ids = [
        worker_env.add_job(status=JobStatus.QUEUED, position=p) for p in (1, 2, 3)
    ]

    with Session(worker_env.engine) as s:
        asyncio.run(move_job(ids[2], direction="up", session=s))

    with Session(worker_env.engine) as s:
        order = [
            j.id
            for j in s.exec(
                select(Job)
                .where(Job.status == JobStatus.QUEUED)
                .order_by(Job.position, Job.created_at)
            ).all()
        ]
    # el tercero subió por encima del segundo
    assert order.index(ids[2]) < order.index(ids[1])


def test_move_at_edge_is_noop(worker_env):
    ids = [worker_env.add_job(status=JobStatus.QUEUED, position=p) for p in (1, 2)]
    with Session(worker_env.engine) as s:
        asyncio.run(move_job(ids[0], direction="up", session=s))  # ya es el primero
    with Session(worker_env.engine) as s:
        order = [
            j.id
            for j in s.exec(
                select(Job)
                .where(Job.status == JobStatus.QUEUED)
                .order_by(Job.position, Job.created_at)
            ).all()
        ]
    assert order == ids
