"""
Synchronous database session for Streamlit pages.
Streamlit runs its own event loop — asyncio.run() inside page
functions causes "Future attached to a different loop" errors.
This module provides a plain sync psycopg2/SQLAlchemy session instead.
"""
import re
import ssl
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _sync_url() -> str:
    url = settings.DATABASE_URL_SYNC or settings.DATABASE_URL
    # Strip async driver prefix
    url = re.sub(r"postgresql\+asyncpg://", "postgresql+psycopg2://", url)
    url = re.sub(r"sqlite\+aiosqlite://", "sqlite://", url)
    # Remove sslrootcert if present (causes conflict)
    url = re.sub(r"[&?]sslrootcert=[^&]*", "", url)
    # Ensure sslmode=require
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


_engine = create_engine(
    _sync_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SyncSessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


@contextmanager
def get_sync_db():
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
