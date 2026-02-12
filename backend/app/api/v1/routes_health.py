from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from fastapi import Depends

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | float]:
    db_status = "ok"
    redis_status = "ok"

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        redis_client: Redis | None = getattr(request.app.state, "redis", None)
        if redis_client is None:
            redis_status = "not_configured"
        else:
            await redis_client.ping()
    except Exception:
        redis_status = "error"

    started_at: datetime = request.app.state.started_at
    uptime = (datetime.now(tz=UTC) - started_at).total_seconds()

    return {
        "status": "ok" if db_status == "ok" and redis_status in {"ok", "not_configured"} else "degraded",
        "db": db_status,
        "redis": redis_status,
        "uptime": uptime,
    }
