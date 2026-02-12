from __future__ import annotations

import logging
import os

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base

logger = logging.getLogger(__name__)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def should_create_all(database_url: str) -> bool:
    override = os.getenv("DB_CREATE_ALL", "").strip() == "1"
    if override:
        return True
    return database_url.startswith("sqlite")


def _ensure_initialized() -> None:
    global _engine, _session_factory
    if _engine is None:
        from app.core.config import get_settings

        settings = get_settings()
        try:
            _engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
            _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
        except SQLAlchemyError:
            logger.exception("Nie udało się zainicjalizować silnika bazy danych.")
            raise


def get_engine() -> AsyncEngine:
    _ensure_initialized()
    assert _engine is not None
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    _ensure_initialized()
    assert _session_factory is not None
    return _session_factory


async def init_db() -> None:
    from app.core.config import get_settings

    engine = get_engine()
    database_url = get_settings().DATABASE_URL
    if not should_create_all(database_url):
        logger.info("Skipping create_all; rely on Alembic migrations")
        return

    import app.db.models  # noqa: F401

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError:
        logger.exception("Nie udało się utworzyć schematu bazy danych.")
        raise
