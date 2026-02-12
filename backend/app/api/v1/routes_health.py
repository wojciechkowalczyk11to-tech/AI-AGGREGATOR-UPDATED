from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

router = APIRouter(tags=['health'])

HEALTH_CHECK_TIMEOUT = 5.0


@router.get('/health')
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    db_status = 'ok'
    redis_status = 'ok'

    try:
        await asyncio.wait_for(db.execute(text('SELECT 1')), timeout=HEALTH_CHECK_TIMEOUT)
    except (asyncio.TimeoutError, Exception):
        db_status = 'error'

    try:
        redis_client: Redis | None = getattr(request.app.state, 'redis', None)
        if redis_client is None:
            redis_status = 'error'
        else:
            await asyncio.wait_for(redis_client.ping(), timeout=HEALTH_CHECK_TIMEOUT)
    except (asyncio.TimeoutError, Exception):
        redis_status = 'error'

    started_at: datetime = request.app.state.started_at
    uptime = (datetime.now(tz=timezone.utc) - started_at).total_seconds()

    return {
        'status': 'healthy' if db_status == 'ok' and redis_status == 'ok' else 'degraded',
        'checks': {'db': db_status, 'redis': redis_status},
        'uptime_seconds': round(uptime, 2),
    }
