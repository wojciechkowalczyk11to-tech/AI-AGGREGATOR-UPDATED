from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

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
    logger.info('Backend starting up')

    app.state.started_at = datetime.now(tz=timezone.utc)

    try:
        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        app.state.redis = redis_client
        logger.info('Redis connected')
    except Exception:
        logger.warning('Redis unavailable at startup')
        app.state.redis = None

    try:
        await init_db()
        logger.info('Database initialized')
    except Exception:
        logger.error('Database initialization failed', exc_info=True)
        raise

    yield

    if app.state.redis is not None:
        await app.state.redis.aclose()
    engine = get_engine()
    await engine.dispose()
    logger.info('Backend shut down')


def create_app() -> FastAPI:
    app = FastAPI(title='JARVIS AI Aggregator', version='0.1.0', lifespan=lifespan)
    app.include_router(api_router, prefix='/api/v1')

    @app.exception_handler(JarvisBaseError)
    async def jarvis_error_handler(request: Request, exc: JarvisBaseError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})

    return app
