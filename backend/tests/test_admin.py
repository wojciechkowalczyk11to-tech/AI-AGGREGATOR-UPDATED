from __future__ import annotations

import os

import pytest

from app.core.config import get_settings
from app.db.models import UsageLedger, User, UserRole


@pytest.fixture
def admin_env() -> None:
    os.environ["ADMIN_USER_IDS"] = "1001"
    get_settings.cache_clear()
    yield
    os.environ["ADMIN_USER_IDS"] = ""
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_admin_overview(async_client, test_session, admin_env) -> None:
    admin_user = User(telegram_id=1001, role=UserRole.FULL_ACCESS, authorized=True, verified=True)
    regular_user = User(telegram_id=1002, role=UserRole.DEMO, authorized=True)
    test_session.add_all([admin_user, regular_user])
    await test_session.commit()

    ledger = UsageLedger(
        user_id=admin_user.id,
        provider="gemini",
        model="gemini-1.5-flash",
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.1,
    )
    test_session.add(ledger)
    await test_session.commit()

    register = await async_client.post("/api/v1/auth/register", json={"telegram_chat_id": 1001})
    token = register.json()["access_token"]

    response = await async_client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] >= 2
    assert "gemini" in data["providers_available"]


@pytest.mark.asyncio
async def test_admin_list_users(async_client, test_session, admin_env) -> None:
    admin_user = User(telegram_id=1001, role=UserRole.FULL_ACCESS, authorized=True, verified=True)
    listed_user = User(telegram_id=2002, role=UserRole.DEMO, authorized=True)
    test_session.add_all([admin_user, listed_user])
    await test_session.commit()

    register = await async_client.post("/api/v1/auth/register", json={"telegram_chat_id": 1001})
    token = register.json()["access_token"]

    response = await async_client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert any(item["telegram_id"] == 2002 for item in response.json())


@pytest.mark.asyncio
async def test_admin_add_user(async_client, test_session, admin_env) -> None:
    admin_user = User(telegram_id=1001, role=UserRole.FULL_ACCESS, authorized=True, verified=True)
    test_session.add(admin_user)
    await test_session.commit()

    register = await async_client.post("/api/v1/auth/register", json={"telegram_chat_id": 1001})
    token = register.json()["access_token"]

    response = await async_client.post(
        "/api/v1/admin/users",
        json={"telegram_id": 3333, "role": "FULL_ACCESS"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "FULL_ACCESS"


@pytest.mark.asyncio
async def test_admin_not_admin_rejected(async_client, test_session, admin_env) -> None:
    regular_user = User(telegram_id=4444, role=UserRole.DEMO, authorized=True)
    test_session.add(regular_user)
    await test_session.commit()

    register = await async_client.post("/api/v1/auth/register", json={"telegram_chat_id": 4444})
    token = register.json()["access_token"]

    response = await async_client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
