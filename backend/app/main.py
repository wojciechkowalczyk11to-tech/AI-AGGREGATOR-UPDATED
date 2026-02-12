from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import JarvisBaseError
from app.core.logging_config import setup_logging
from app.db.session import get_engine, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(level=settings.LOG_LEVEL, json_mode=settings.LOG_JSON)
    app.state.started_at = datetime.now(tz=timezone.utc)
    app.state.redis = None

    try:
        app.state.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await app.state.redis.ping()
    except Exception:
        logger.warning("Nie udało się połączyć z Redis podczas uruchamiania.", exc_info=True)
        app.state.redis = None

    try:
        await init_db()
        logger.info("Backend started")
        yield
    finally:
        redis_client: Redis | None = getattr(app.state, "redis", None)
        if redis_client is not None:
            try:
                await redis_client.aclose()
            except Exception:
                logger.warning("Nie udało się poprawnie zamknąć połączenia Redis.", exc_info=True)

        try:
            await get_engine().dispose()
        except Exception:
            logger.warning("Nie udało się poprawnie zamknąć silnika bazy danych.", exc_info=True)

        logger.info("Backend stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="JARVIS AI Aggregator",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(JarvisBaseError)
    async def jarvis_error_handler(request: Request, exc: JarvisBaseError) -> JSONResponse:
        _ = request
        payload: dict[str, Any] = {
            "error": {
                "type": exc.__class__.__name__,
                "detail": exc.detail,
            }
        }
        return JSONResponse(status_code=exc.status_code, content=payload)

    return app
