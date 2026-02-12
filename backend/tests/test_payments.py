from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import get_settings
from app.db.models import User, UserRole
from app.services.payment_service import payment_service
from app.services.policy_engine import PolicyEngine


@pytest.mark.asyncio
async def test_get_plans_returns_all() -> None:
    plans = await payment_service.get_plans()
    ids = {plan["id"] for plan in plans}
    assert ids == {"free", "starter", "pro", "unlimited"}


@pytest.mark.asyncio
async def test_create_invoice_valid_plan() -> None:
    invoice = await payment_service.create_invoice("starter")
    assert invoice["currency"] == "XTR"
    assert invoice["payload"] == "starter"
    assert invoice["prices"][0]["amount"] == 50


@pytest.mark.asyncio
async def test_create_invoice_invalid_plan_raises() -> None:
    with pytest.raises(ValueError, match="Nieprawidłowy"):
        await payment_service.create_invoice("vip")


@pytest.mark.asyncio
async def test_create_invoice_free_plan_raises() -> None:
    with pytest.raises(ValueError, match="darmowy"):
        await payment_service.create_invoice("free")


@pytest.mark.asyncio
async def test_process_payment_activates_subscription(test_session) -> None:
    user = User(telegram_id=4101, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()

    payment = await payment_service.process_payment(
        user_id=user.id,
        plan_id="pro",
        stars_amount=200,
        telegram_charge_id="charge-4101",
        db=test_session,
    )

    await test_session.refresh(user)
    assert payment.plan == "pro"
    assert payment.stars_amount == 200
    assert user.subscription_tier == "pro"
    assert user.subscription_expires_at is not None
    assert user.subscription_expires_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_check_subscription_active(test_session) -> None:
    user = User(
        telegram_id=4102,
        role=UserRole.DEMO,
        authorized=True,
        subscription_tier="starter",
        subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=2),
    )
    test_session.add(user)
    await test_session.commit()

    status = await payment_service.check_subscription(user, test_session)
    assert status["active"] is True
    assert status["tier"] == "starter"


@pytest.mark.asyncio
async def test_check_subscription_expired(test_session) -> None:
    user = User(
        telegram_id=4103,
        role=UserRole.DEMO,
        authorized=True,
        subscription_tier="starter",
        subscription_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    test_session.add(user)
    await test_session.commit()

    status = await payment_service.check_subscription(user, test_session)
    await test_session.refresh(user)
    assert status["active"] is False
    assert user.subscription_tier == "free"
    assert user.subscription_expires_at is None


@pytest.mark.asyncio
async def test_refund_downgrades_user(test_session) -> None:
    user = User(telegram_id=4104, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()

    payment = await payment_service.process_payment(
        user_id=user.id,
        plan_id="unlimited",
        stars_amount=500,
        telegram_charge_id="charge-4104",
        db=test_session,
    )
    refunded = await payment_service.refund(payment.id, test_session)
    await test_session.refresh(user)

    assert refunded.status == "refunded"
    assert user.subscription_tier == "free"


@pytest.mark.asyncio
async def test_policy_engine_starter_smart_unlimited(test_session) -> None:
    user = User(
        telegram_id=4105,
        role=UserRole.DEMO,
        authorized=True,
        subscription_tier="starter",
        subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    test_session.add(user)
    await test_session.commit()

    engine = PolicyEngine()
    limits = engine.get_effective_limits(user)
    result = await engine.check_access(user, "gemini", test_session, get_settings())
    assert limits["smart_unlimited"] is True
    assert result.allowed is True


@pytest.mark.asyncio
async def test_policy_engine_pro_all_providers(test_session) -> None:
    user = User(
        telegram_id=4106,
        role=UserRole.DEMO,
        authorized=True,
        subscription_tier="pro",
        subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    test_session.add(user)
    await test_session.commit()

    engine = PolicyEngine()
    openai_result = await engine.check_access(user, "openai", test_session, get_settings())
    anthropic_result = await engine.check_access(user, "anthropic", test_session, get_settings())
    assert openai_result.allowed is True
    assert anthropic_result.allowed is True


@pytest.mark.asyncio
async def test_policy_engine_free_blocked_gpt(test_session) -> None:
    user = User(telegram_id=4107, role=UserRole.DEMO, authorized=True, subscription_tier="free")
    test_session.add(user)
    await test_session.commit()

    engine = PolicyEngine()
    result = await engine.check_access(user, "openai", test_session, get_settings())
    assert result.allowed is False
