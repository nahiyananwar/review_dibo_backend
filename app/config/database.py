"""Database configuration.

Owns the SQLAlchemy engine, session factory, declarative ``Base`` and the
``get_db`` FastAPI dependency. The engine is driven entirely by ``DATABASE_URL``
so the same code targets PostgreSQL (production) or SQLite (quick local checks).
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.config import settings


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        # SQLite needs this to be usable across FastAPI's threadpool.
        return {"connect_args": {"check_same_thread": False}}
    # PostgreSQL: recycle dead connections gracefully.
    return {"pool_pre_ping": True}


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@event.listens_for(Engine, "connect")
def _enforce_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """SQLite ignores FK constraints unless explicitly enabled per connection.

    No-op for PostgreSQL (which always enforces them).
    """
    if settings.is_sqlite:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def import_models() -> None:
    """Import every ORM model so they register on ``Base.metadata``.

    Imported lazily (inside the function) to avoid a circular import, since the
    models import ``Base`` from this module. Used by Alembic and ``init_db``.
    """
    from app.modules.products.models import Product  # noqa: F401
    from app.modules.reviews.models import Review  # noqa: F401
    from app.modules.users.models import User  # noqa: F401


def init_db() -> None:
    """Create all tables directly (local/dev convenience).

    Production uses Alembic migrations (``alembic upgrade head``); this is a
    shortcut for quick local runs and the seed script.
    """
    import_models()
    Base.metadata.create_all(bind=engine)
