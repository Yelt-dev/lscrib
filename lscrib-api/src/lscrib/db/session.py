"""Engine SQLite y utilidades de sesión."""

from collections.abc import Iterator

from sqlmodel import Session, create_engine

from lscrib.config import settings

# check_same_thread=False: el worker en proceso y la API comparten el engine.
# timeout: espera si la BD está bloqueada por la otra parte, en vez de reventar.
engine = create_engine(
    settings.db_url,
    connect_args={"check_same_thread": False, "timeout": 30},
)


def init_db() -> None:
    """Aplica las migraciones pendientes. Llamado en el arranque de la app.

    Antes usaba `create_all`, que no altera tablas ya existentes; ahora Alembic
    lleva el esquema a `head` (crea la BD en instalaciones nuevas y migra las
    viejas). Ver `lscrib.db.migrate`.
    """
    import lscrib.db.models  # noqa: F401  (registra los modelos en metadata)
    from lscrib.db.migrate import run_migrations

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    run_migrations()


def get_session() -> Iterator[Session]:
    """Dependencia FastAPI: una sesión por request."""
    with Session(engine) as session:
        yield session


def recover_stuck_jobs() -> None:
    """Al arrancar, cualquier job in-progress quedó huérfano tras un reinicio.

    No hay worker que lo continúe, así que se marca `failed` con un mensaje claro
    (R14). El usuario puede reintentar (failed → queued, doc 07).
    """
    from sqlmodel import select

    from lscrib.db.models import Job
    from lscrib.domain.models import JobStatus

    in_progress = {JobStatus.QUEUED, JobStatus.NORMALIZING, JobStatus.TRANSCRIBING}
    with Session(engine) as session:
        stuck = session.exec(select(Job).where(Job.status.in_(in_progress))).all()
        for job in stuck:
            job.status = JobStatus.FAILED
            job.error = "Interrumpido por un reinicio del servidor. Reintenta."
            session.add(job)
        if stuck:
            session.commit()
