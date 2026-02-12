from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.config import get_settings
from backend.app.db.base import Base
import backend.app.db.models  # noqa: F401

_settings = get_settings()
_engine: AsyncEngine = create_async_engine(_settings.DATABASE_URL, future=True, echo=False)
_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine() -> AsyncEngine:
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return _session_factory


async def init_db() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
