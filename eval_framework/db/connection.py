"""Database connection setup.

Uses scoped_session per thread so that concurrent L1 execution
via ThreadPoolExecutor doesn't share SQLite connections.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from eval_framework.config import config

_engine = None
_SessionFactory = None


def get_engine():
    global _engine
    if _engine is None:
        url = config.get_database_url()
        kwargs: dict = {}
        # SQLite needs these for multi-threaded access
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            kwargs["poolclass"] = __import__("sqlalchemy.pool").pool.StaticPool
        _engine = create_engine(
            url,
            echo=False,
            pool_pre_ping=True,
            **kwargs,
        )
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
