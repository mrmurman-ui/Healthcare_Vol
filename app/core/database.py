import ssl

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _make_engine():
    url = settings.DATABASE_URL

    # Strip sslmode — asyncpg uses connect_args ssl instead
    url = url.replace("?sslmode=require", "").replace("&sslmode=require", "")
    url = url.replace("?prepared_statement_cache_size=0", "")
    url = url.replace("&prepared_statement_cache_size=0", "")

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    return create_async_engine(
        url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={
            "ssl": ssl_ctx,
            # Disable prepared statement cache for PgBouncer compatibility
            "statement_cache_size": 0,
        },
    )


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
