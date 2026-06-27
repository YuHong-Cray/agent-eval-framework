"""Database connection setup.

Thread-safe SQLite: WAL journal mode + write lock in repository.
Each thread gets its own session; commits are serialized via _write_lock.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from eval_framework.config import config

_engine = None
_SessionFactory = None


def get_engine():
    global _engine
    if _engine is None:
        url = config.get_database_url()
        kwargs: dict = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        else:
            kwargs["pool_pre_ping"] = True

        _engine = create_engine(url, echo=False, **kwargs)

        # Enable WAL mode for SQLite — allows concurrent reads + single writer
        if url.startswith("sqlite"):

            @event.listens_for(_engine, "connect")
            def _set_wal(dbapi_conn, _rec):
                dbapi_conn.execute("PRAGMA journal_mode=WAL")
                dbapi_conn.execute("PRAGMA busy_timeout=5000")

    return _engine


def get_session() -> Session:
    """Return a new session (one per call, not shared across threads)."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory()


def init_db():
    """Create all tables."""
    from eval_framework.db.models import Base

    Base.metadata.create_all(get_engine())
