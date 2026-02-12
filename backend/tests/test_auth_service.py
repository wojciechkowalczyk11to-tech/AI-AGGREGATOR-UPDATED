from __future__ import annotations

import uuid

import pytest

from app.core.config import get_settings
from app.core.exceptions import RateLimitExceededError
from app.core.security import verify_token
from app.db.models import User, UserRole
from app.services.auth_service import auth_service


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.data[key] = self.data.get(key, 0) + 1
        return self.data[key]

    async def expire(self, key: str, _: int) -> bool:
        return key in self.data


@pytest.mark.asyncio
async def test_register_new_user(test_session) -> None:
    payload = await auth_service.register(telegram_id=1234567, db=test_session)
    assert payload["telegram_id"] == 1234567
    assert payload["authorized"] is False


@pytest.mark.asyncio
async def test_register_existing_user_idempotent(test_session) -> None:
    first = await auth_service.register(telegram_id=223344, db=test_session)
    second = await auth_service.register(telegram_id=223344, db=test_session)
    assert first["id"] == second["id"]


@pytest.mark.asyncio
async def test_unlock_correct_code(test_session) -> None:
    await auth_service.register(telegram_id=777000, db=test_session)
    out = await auth_service.unlock(
        777000, get_settings().DEMO_UNLOCK_CODE, test_session, FakeRedis()
    )
    assert out["success"] is True


@pytest.mark.asyncio
async def test_unlock_wrong_code(test_session) -> None:
    await auth_service.register(telegram_id=777001, db=test_session)
    out = await auth_service.unlock(777001, "zly-kod", test_session, FakeRedis())
    assert out["success"] is False


@pytest.mark.asyncio
async def test_bootstrap_first_time(test_session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOOTSTRAP_ADMIN_CODE", "admin-123")
    get_settings.cache_clear()
    out = await auth_service.bootstrap(telegram_id=999001, code="admin-123", db=test_session)
    assert out["success"] is True


@pytest.mark.asyncio
async def test_bootstrap_already_has_full(test_session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOOTSTRAP_ADMIN_CODE", "admin-123")
    get_settings.cache_clear()
    test_session.add(User(telegram_id=999002, role=UserRole.FULL_ACCESS, authorized=True))
    await test_session.commit()
    out = await auth_service.bootstrap(telegram_id=999003, code="admin-123", db=test_session)
    assert out["success"] is False


@pytest.mark.asyncio
async def test_jwt_roundtrip(test_session) -> None:
    reg = await auth_service.register(telegram_id=666111, db=test_session)
    payload = verify_token(reg["access_token"])
    assert uuid.UUID(payload["sub"]) is not None


@pytest.mark.asyncio
async def test_unlock_rate_limited(test_session) -> None:
    await auth_service.register(telegram_id=444000, db=test_session)
    redis = FakeRedis()
    for _ in range(5):
        await auth_service.unlock(444000, "wrong", test_session, redis)
    with pytest.raises(RateLimitExceededError):
        await auth_service.unlock(444000, "wrong", test_session, redis)
