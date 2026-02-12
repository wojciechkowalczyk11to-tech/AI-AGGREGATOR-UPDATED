from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import ToolCounter, User, UserRole


@dataclass(slots=True)
class PolicyResult:
    allowed: bool
    denied_reason: str | None
    suggestion: str | None
    budget_remaining: float


class PolicyEngine:
    PROVIDER_ACCESS: dict[UserRole, dict[str, str]] = {
        UserRole.DEMO: {
            "gemini": "unlimited",
            "deepseek": "high",
            "groq": "free",
            "openrouter": "free",
            "grok": "limited",
        },
        UserRole.FULL_ACCESS: {
            "gemini": "full",
            "deepseek": "full",
            "groq": "full",
            "openrouter": "full",
            "grok": "full",
        },
    }
    BLOCKED_COMMANDS: dict[UserRole, list[str]] = {
        UserRole.DEMO: ["/github", "/gpt", "/claude", "/opus", "/deep"],
        UserRole.FULL_ACCESS: [],
    }

    async def check_access(
        self,
        user: User,
        provider: str | None,
        db: AsyncSession,
        settings: Settings,
    ) -> PolicyResult:
        if not user.authorized:
            return PolicyResult(False, "Nie autoryzowany", "Użyj kodu odblokowania", 0.0)

        provider_name = (provider or "gemini").lower()
        role_access = self.PROVIDER_ACCESS.get(user.role, {})
        if provider_name not in role_access:
            return PolicyResult(False, "Brak dostępu do tego providera", "Wybierz gemini", 0.0)

        counter = await self._get_today_counter(user.id, db)
        total_cost = float(counter.total_cost_usd if counter else Decimal("0"))
        budget_remaining = max(settings.FULL_DAILY_USD_CAP - total_cost, 0.0)

        if user.role == UserRole.DEMO and provider_name == "grok":
            used = counter.grok_calls if counter else 0
            if used >= settings.DEMO_GROK_DAILY:
                return PolicyResult(
                    False, "Przekroczono limit", "Spróbuj providera gemini", budget_remaining
                )

        if (
            user.role == UserRole.DEMO
            and (counter.smart_credits_used if counter else 0) >= settings.DEMO_SMART_CREDITS_DAILY
        ):
            return PolicyResult(
                False, "Przekroczono limit", "Przełącz na tryb eco", budget_remaining
            )

        if budget_remaining <= 0:
            return PolicyResult(False, "Przekroczono limit", "Spróbuj jutro", 0.0)

        return PolicyResult(True, None, None, budget_remaining)

    def check_command(self, user: User, command: str) -> bool:
        blocked = self.BLOCKED_COMMANDS.get(user.role, [])
        return command not in blocked

    def get_provider_chain(self, user: User, profile: str) -> list[str]:
        _ = profile
        if user.role == UserRole.DEMO:
            return ["gemini", "groq", "openrouter"]
        return ["gemini", "deepseek", "groq", "openrouter", "grok"]

    async def increment_counters(
        self,
        user: User,
        provider: str,
        cost: float,
        smart_credits: int,
        db: AsyncSession,
    ) -> None:
        counter = await self._get_today_counter(user.id, db)
        if counter is None:
            counter = ToolCounter(user_id=user.id, date=date.today())
            db.add(counter)

        if provider.lower() == "grok":
            counter.grok_calls += 1
        if provider.lower() in {"openrouter", "gemini"}:
            counter.web_calls += 1

        counter.smart_credits_used += smart_credits
        counter.total_cost_usd = Decimal(counter.total_cost_usd) + Decimal(str(cost))
        await db.commit()

    async def get_remaining_limits(
        self,
        user: User,
        db: AsyncSession,
        settings: Settings,
    ) -> dict[str, Any]:
        counter = await self._get_today_counter(user.id, db)
        used_grok = counter.grok_calls if counter else 0
        used_credits = counter.smart_credits_used if counter else 0
        used_cost = float(counter.total_cost_usd if counter else Decimal("0"))
        return {
            "grok_remaining": max(settings.DEMO_GROK_DAILY - used_grok, 0),
            "smart_credits_remaining": max(settings.DEMO_SMART_CREDITS_DAILY - used_credits, 0),
            "daily_budget_remaining": max(settings.FULL_DAILY_USD_CAP - used_cost, 0.0),
        }

    async def _get_today_counter(self, user_id: Any, db: AsyncSession) -> ToolCounter | None:
        result = await db.execute(
            select(ToolCounter).where(
                ToolCounter.user_id == user_id, ToolCounter.date == date.today()
            )
        )
        return result.scalar_one_or_none()


policy_engine = PolicyEngine()
