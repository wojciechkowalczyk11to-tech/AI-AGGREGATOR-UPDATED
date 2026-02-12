from __future__ import annotations


import pytest
from sqlalchemy import select

from app.core.exceptions import PolicyDeniedError
from app.db.models import UsageLedger, User, UserRole
from app.providers.base import AbstractProvider, ProviderResult
from app.providers.factory import ProviderFactory
from app.services.orchestrator import Orchestrator
from app.services.policy_engine import PolicyEngine
from app.services.usage_service import UsageService


class MockGeminiProvider(AbstractProvider):
    @property
    def name(self) -> str:
        return "gemini"

    async def generate(
        self,
        messages: list[dict[str, str]],
        profile: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResult:
        _ = (messages, profile, max_tokens, temperature)
        return ProviderResult(
            text="Wynik testowy",
            provider="gemini",
            model="gemini-2.0-flash-lite",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001,
            latency_ms=10,
        )

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_eco_chat_success(test_session) -> None:
    user = User(telegram_id=3001, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()

    factory = ProviderFactory.__new__(ProviderFactory)
    factory._registry = {"gemini": MockGeminiProvider()}  # type: ignore[attr-defined]
    orchestrator = Orchestrator(PolicyEngine(), factory, UsageService())

    result = await orchestrator.process_chat(
        user=user,
        prompt="Hej",
        session_id=None,
        provider_pref="gemini",
        mode="eco",
        db=test_session,
    )
    assert result["response"] == "Wynik testowy"


@pytest.mark.asyncio
async def test_demo_blocked_provider(test_session) -> None:
    user = User(telegram_id=3002, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()

    factory = ProviderFactory.__new__(ProviderFactory)
    factory._registry = {"gemini": MockGeminiProvider()}  # type: ignore[attr-defined]
    orchestrator = Orchestrator(PolicyEngine(), factory, UsageService())

    with pytest.raises(PolicyDeniedError):
        await orchestrator.process_chat(
            user=user,
            prompt="Hej",
            session_id=None,
            provider_pref="gpt",
            mode="eco",
            db=test_session,
        )


@pytest.mark.asyncio
async def test_usage_logged_after_chat(test_session) -> None:
    user = User(telegram_id=3003, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()

    factory = ProviderFactory.__new__(ProviderFactory)
    factory._registry = {"gemini": MockGeminiProvider()}  # type: ignore[attr-defined]
    orchestrator = Orchestrator(PolicyEngine(), factory, UsageService())

    await orchestrator.process_chat(
        user=user,
        prompt="Hej",
        session_id=None,
        provider_pref="gemini",
        mode="eco",
        db=test_session,
    )
    result = await test_session.execute(select(UsageLedger).where(UsageLedger.user_id == user.id))
    assert result.scalar_one_or_none() is not None
