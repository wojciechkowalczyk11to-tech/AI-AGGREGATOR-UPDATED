from __future__ import annotations

import pytest

from app.core.config import get_settings


def _has_aiosqlite() -> bool:
    try:
        import aiosqlite  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


pytestmark = pytest.mark.skipif(not _has_aiosqlite(), reason="Brak zależności aiosqlite w środowisku testowym.")


@pytest.mark.asyncio
async def test_register_endpoint(async_client) -> None:
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"telegram_chat_id": 818181},
    )
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200
    assert response.json()["telegram_id"] == 818181


@pytest.mark.asyncio
async def test_unlock_endpoint(async_client) -> None:
    await async_client.post("/api/v1/auth/register", json={"telegram_chat_id": 828282})
    response = await async_client.post(
        "/api/v1/auth/unlock",
        json={"telegram_chat_id": 828282, "code": get_settings().DEMO_UNLOCK_CODE},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_me_endpoint(async_client) -> None:
    register = await async_client.post("/api/v1/auth/register", json={"telegram_chat_id": 838383})
    token = register.json()["access_token"]
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["telegram_id"] == 838383
