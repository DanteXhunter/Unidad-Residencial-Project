"""Motor de SQLAlchemy y dependencia de sesión para FastAPI."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def _connect_args(url: str) -> dict:
    """Ajustes de conexión específicos de Supabase.

    El *transaction pooler* de Supabase (puerto 6543) multiplexa conexiones y no
    soporta sentencias preparadas: psycopg falla con "prepared statement already
    exists". Desactivarlas es obligatorio en ese modo.
    """
    args: dict = {}
    if "pooler.supabase.com" in url:
        args["sslmode"] = "require"
        if ":6543" in url:
            args["prepare_threshold"] = None
    return args


engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=True,  # descarta conexiones muertas por el pooler
    pool_size=5,
    max_overflow=5,
    connect_args=_connect_args(settings.sqlalchemy_url),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependencia de FastAPI: abre una sesión por request y la cierra siempre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
