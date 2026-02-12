from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _ensure_initialized() -> None:
    global _engine, _session_factory
    if _engine is None:
        from app.core.config import get_settings

        settings = get_settings()
        _engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine() -> AsyncEngine:
    _ensure_initialized()
    assert _engine is not None
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    _ensure_initialized()
    assert _session_factory is not None
    return _session_factory


async def init_db() -> None:
    engine = get_engine()
    import app.db.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
