"""Database connection setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from eval_framework.config import config

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.get_database_url(),
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def init_db():
    """Create all tables."""
    from eval_framework.db.models import Base

    Base.metadata.create_all(get_engine())
