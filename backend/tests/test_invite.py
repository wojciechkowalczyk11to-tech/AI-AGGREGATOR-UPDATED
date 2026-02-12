from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.db.models import InviteCode, User, UserRole
from app.services.invite_service import invite_service


@pytest.mark.asyncio
async def test_create_invite(test_session) -> None:
    code = await invite_service.create_invite(123, "DEMO", 2, 2, test_session)
    assert isinstance(code, str)
    assert len(code) == 32


@pytest.mark.asyncio
async def test_validate_invite(test_session) -> None:
    code = await invite_service.create_invite(123, "FULL_ACCESS", 2, 1, test_session)
    role = await invite_service.validate_invite(code, test_session)
    assert role == "FULL_ACCESS"


@pytest.mark.asyncio
async def test_consume_invite(test_session) -> None:
    code = await invite_service.create_invite(123, "FULL_ACCESS", 2, 1, test_session)
    result = await invite_service.consume_invite(code, 7777, test_session)

    assert result["success"] is True
    assert result["role"] == "FULL_ACCESS"


@pytest.mark.asyncio
async def test_invite_expired(test_session) -> None:
    expired = InviteCode(
        code_hash=invite_service._hash_code("expired-code"),
        role=UserRole.DEMO,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        uses_left=1,
        created_by=999,
    )
    test_session.add(expired)
    await test_session.commit()

    role = await invite_service.validate_invite("expired-code", test_session)
    consume = await invite_service.consume_invite("expired-code", 5555, test_session)

    assert role is None
    assert consume["success"] is False


@pytest.mark.asyncio
async def test_consume_invite_upgrades_existing_user(test_session) -> None:
    user = User(telegram_id=8888, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()

    code = await invite_service.create_invite(123, "FULL_ACCESS", 1, 1, test_session)
    result = await invite_service.consume_invite(code, 8888, test_session)
    await test_session.refresh(user)

    assert result["success"] is True
    assert user.role == UserRole.FULL_ACCESS
