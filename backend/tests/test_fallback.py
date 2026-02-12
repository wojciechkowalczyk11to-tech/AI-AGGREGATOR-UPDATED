from __future__ import annotations

import pytest

from app.core.exceptions import AllProvidersFailedError, ProviderError
from app.db.models import User, UserRole
from app.providers.base import AbstractProvider, ProviderResult
from app.providers.factory import ProviderFactory
from app.services.orchestrator import Orchestrator
from app.services.policy_engine import PolicyEngine
from app.services.usage_service import UsageService


class FailingProvider(AbstractProvider):
    @property
    def name(self) -> str:
        return "deepseek"

    async def generate(
        self,
        messages: list[dict[str, str]],
        profile: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResult:
        _ = (messages, profile, max_tokens, temperature)
        raise ProviderError("Provider celowo nie działa")

    async def health_check(self) -> bool:
        return False


class SuccessProvider(AbstractProvider):
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
            text="Odpowiedź zapasowa",
            provider="gemini",
            model="gemini-2.0-flash-lite",
            input_tokens=50,
            output_tokens=30,
            cost_usd=0.0,
            latency_ms=12,
        )

    async def health_check(self) -> bool:
        return True


class SuccessGeminiProvider(AbstractProvider):
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
        return ProviderResult(
            text="Odpowiedź zapasowa",
            provider="gemini",
            model="gemini-2.0-flash-lite",
            input_tokens=50,
            output_tokens=30,
            cost_usd=0.0,
            latency_ms=12,
        )

    async def health_check(self) -> bool:
        return True


class FailingGeminiProvider(AbstractProvider):
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
        raise ProviderError("Gemini failed")

    async def health_check(self) -> bool:
        return False


class SuccessDeepseekProvider(AbstractProvider):
    @property
    def name(self) -> str:
        return "deepseek"

    async def generate(
        self,
        messages: list[dict[str, str]],
        profile: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResult:
        return ProviderResult(
            text="Odpowiedź z Deepseek",
            provider="deepseek",
            model="deepseek-chat",
            input_tokens=50,
            output_tokens=30,
            cost_usd=0.0,
            latency_ms=12,
        )

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_primary_fails_secondary_succeeds(test_session) -> None:
    user = User(telegram_id=4101, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()

    factory = ProviderFactory.__new__(ProviderFactory)
    # Gemini is first in chain, so making it fail should trigger Deepseek
    factory._registry = {
        "gemini": FailingGeminiProvider(),
        "deepseek": SuccessDeepseekProvider(),
    }  # type: ignore[attr-defined]
    orchestrator = Orchestrator(PolicyEngine(), factory, UsageService())

    response = await orchestrator.process_chat(
        user=user,
        prompt="Wyjaśnij pojęcie",
        session_id=None,
        provider_pref=None,
        mode="eco",
        db=test_session,
    )

    assert response["response"] == "Odpowiedź z Deepseek"
    assert response["meta"]["fallback_used"] is True


@pytest.mark.asyncio
async def test_all_providers_fail_raises(test_session) -> None:
    user = User(telegram_id=4102, role=UserRole.DEMO, authorized=True)
    test_session.add(user)
    await test_session.commit()

    factory = ProviderFactory.__new__(ProviderFactory)
    factory._registry = {"deepseek": FailingProvider()}  # type: ignore[attr-defined]
    orchestrator = Orchestrator(PolicyEngine(), factory, UsageService())

    with pytest.raises(AllProvidersFailedError):
        await orchestrator.process_chat(
            user=user,
            prompt="Wyjaśnij pojęcie",
            session_id=None,
            provider_pref="deepseek",
            mode="eco",
            db=test_session,
        )
