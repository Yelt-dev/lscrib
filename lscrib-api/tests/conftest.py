"""Fixtures compartidas: entorno de worker aislado (BD + data_dir temporales)."""

from pathlib import Path
from uuid import uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import lscrib.worker.queue as wq
from lscrib.config import settings
from lscrib.db.models import Job, Segment
from lscrib.domain.models import JobStatus, MediaType


class WorkerEnv:
    """Acceso a la BD temporal del test + helper para crear jobs."""

    def __init__(self, engine, data_dir: Path) -> None:
        self.engine = engine
        self.data_dir = data_dir

    def add_job(self, **overrides) -> str:
        defaults = dict(
            original_filename="sample.mp3",
            file_hash=uuid4().hex,
            media_path=str(self.data_dir / "sample.mp3"),
            media_type=MediaType.AUDIO,
            model="tiny",
            status=JobStatus.QUEUED,
        )
        defaults.update(overrides)
        job = Job(**defaults)
        with Session(self.engine) as s:
            s.add(job)
            s.commit()
            s.refresh(job)
            return job.id

    def get(self, job_id: str) -> Job | None:
        with Session(self.engine) as s:
            return s.get(Job, job_id)

    def segments(self, job_id: str) -> list[Segment]:
        with Session(self.engine) as s:
            return list(
                s.exec(
                    select(Segment)
                    .where(Segment.job_id == job_id)
                    .order_by(Segment.index)
                ).all()
            )


@pytest.fixture
def worker_env(tmp_path, monkeypatch) -> WorkerEnv:
    """Apunta el worker a una SQLite y un data_dir temporales, aislados por test."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # El worker resuelve engine/data_dir en tiempo de ejecución desde estos nombres.
    monkeypatch.setattr(wq, "engine", engine)
    monkeypatch.setattr(settings, "data_dir", data_dir)

    return WorkerEnv(engine, data_dir)
