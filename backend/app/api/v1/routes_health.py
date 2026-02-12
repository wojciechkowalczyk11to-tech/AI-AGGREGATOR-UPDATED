from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

router = APIRouter(tags=["health"])

HEALTH_CHECK_TIMEOUT_SECONDS = 5.0


async def _check_database(db: AsyncSession) -> str:
    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=HEALTH_CHECK_TIMEOUT_SECONDS)
    except TimeoutError:
        return "Przekroczono limit czasu połączenia z bazą danych"
    except Exception as exc:
        return f"Błąd bazy danych: {exc}"
    return "ok"


async def _check_redis(redis_client: Redis | None) -> str:
    if redis_client is None:
        return "Klient Redis nie jest dostępny"

    try:
        await asyncio.wait_for(redis_client.ping(), timeout=HEALTH_CHECK_TIMEOUT_SECONDS)
    except TimeoutError:
        return "Przekroczono limit czasu połączenia z Redis"
    except Exception as exc:
        return f"Błąd Redis: {exc}"
    return "ok"


@router.get("/health")
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    db_status = await _check_database(db)
    redis_client: Redis | None = getattr(request.app.state, "redis", None)
    redis_status = await _check_redis(redis_client)

    started_at: datetime = getattr(request.app.state, "started_at", datetime.now(tz=timezone.utc))
    uptime_seconds = (datetime.now(tz=timezone.utc) - started_at).total_seconds()

    overall_status = "healthy" if db_status == "ok" and redis_status == "ok" else "degraded"

    return {
        "status": overall_status,
        "checks": {
            "db": db_status,
            "redis": redis_status,
        },
        "uptime_seconds": uptime_seconds,
    }
