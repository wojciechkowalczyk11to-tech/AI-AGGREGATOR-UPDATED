from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.db.models import User, UserRole
from app.services.policy_engine import PolicyEngine


@pytest.mark.asyncio
async def test_demo_allowed_gemini(test_session) -> None:
    user = User(telegram_id=1001, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()
    engine = PolicyEngine()
    result = await engine.check_access(user, "gemini", test_session, get_settings())
    assert result.allowed is True


@pytest.mark.asyncio
async def test_demo_blocked_gpt(test_session) -> None:
    user = User(telegram_id=1002, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()
    engine = PolicyEngine()
    result = await engine.check_access(user, "gpt", test_session, get_settings())
    assert result.allowed is False


def test_demo_blocked_github_command() -> None:
    user = User(telegram_id=1003, role=UserRole.DEMO, authorized=True)
    engine = PolicyEngine()
    assert engine.check_command(user, "/github") is False


@pytest.mark.asyncio
async def test_full_access_everything_allowed(test_session) -> None:
    user = User(telegram_id=1004, role=UserRole.FULL_ACCESS, authorized=True)
    test_session.add(user)
    await test_session.commit()
    engine = PolicyEngine()
    result = await engine.check_access(user, "deepseek", test_session, get_settings())
    assert result.allowed is True


@pytest.mark.asyncio
async def test_unauthorized_user_denied(test_session) -> None:
    user = User(telegram_id=1005, role=UserRole.DEMO, authorized=False)
    test_session.add(user)
    await test_session.commit()
    engine = PolicyEngine()
    result = await engine.check_access(user, "gemini", test_session, get_settings())
    assert result.allowed is False


@pytest.mark.asyncio
async def test_increment_counters(test_session) -> None:
    user = User(telegram_id=1006, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()
    engine = PolicyEngine()
    await engine.increment_counters(
        user=user, provider="grok", cost=0.11, smart_credits=2, db=test_session
    )
    limits = await engine.get_remaining_limits(user=user, db=test_session, settings=get_settings())
    assert limits["grok_remaining"] == get_settings().DEMO_GROK_DAILY - 1
