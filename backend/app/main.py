from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from redis.asyncio import Redis

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.logging_config import setup_logging
from backend.app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(level=settings.LOG_LEVEL, json_mode=settings.LOG_JSON)
    app.state.started_at = datetime.now(tz=UTC)

    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    app.state.redis = redis_client

    await init_db()
    try:
        await redis_client.ping()
    except Exception:
        pass

    try:
        yield
    finally:
        await redis_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(title="Ai-Aggregator Backend", version="0.1.0", lifespan=lifespan)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
