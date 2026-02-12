from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.main import create_app


class _FakeRedis:
    def __init__(self, *, should_fail: bool = False) -> None:
        self._should_fail = should_fail

    async def ping(self) -> bool:
        if self._should_fail:
            raise RuntimeError("Redis niedostępny")
        return True


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    app = create_app()
    app.state.started_at = datetime.now(tz=timezone.utc)
    app.state.redis = _FakeRedis()

    mock_db: AsyncMock = AsyncMock()
    mock_db.execute = AsyncMock(return_value=object())

    async def override_get_db() -> AsyncGenerator[Any, None]:
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["checks"]["db"] == "ok"
    assert payload["checks"]["redis"] == "ok"


@pytest.mark.asyncio
async def test_health_db_down() -> None:
    app = create_app()
    app.state.started_at = datetime.now(tz=timezone.utc)
    app.state.redis = _FakeRedis()

    mock_db: AsyncMock = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=RuntimeError("DB padło"))

    async def override_get_db() -> AsyncGenerator[Any, None]:
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["checks"]["db"].startswith("Błąd bazy danych")
    assert payload["checks"]["redis"] == "ok"


@pytest.mark.asyncio
async def test_health_redis_down() -> None:
    app = create_app()
    app.state.started_at = datetime.now(tz=timezone.utc)
    app.state.redis = _FakeRedis(should_fail=True)

    mock_db: AsyncMock = AsyncMock()
    mock_db.execute = AsyncMock(return_value=object())

    async def override_get_db() -> AsyncGenerator[Any, None]:
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["checks"]["db"] == "ok"
    assert payload["checks"]["redis"].startswith("Błąd Redis")
