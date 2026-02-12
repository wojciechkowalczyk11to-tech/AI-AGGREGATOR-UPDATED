from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import ToolCounter, UsageLedger, User, UserRole


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
            "openai": "full",
            "anthropic": "full",
        },
    }
    BLOCKED_COMMANDS: dict[UserRole, list[str]] = {
        UserRole.DEMO: ["/github", "/gpt", "/claude", "/opus", "/deep"],
        UserRole.FULL_ACCESS: [],
    }

    SUBSCRIPTION_LIMITS: dict[str, dict[str, Any]] = {
        "free": {},
        "starter": {
            "smart_unlimited": True,
            "gpt_daily": 5,
            "allowed_providers": {"openai"},
        },
        "pro": {
            "all_providers": True,
            "daily_usd_cap": 2.0,
        },
        "unlimited": {
            "all_providers": True,
            "daily_usd_cap": 5.0,
            "github": True,
        },
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
        limits = self.get_effective_limits(user)
        allowed_providers = limits["allowed_providers"]
        if provider_name not in allowed_providers:
            return PolicyResult(False, "Brak dostępu do tego providera", "Wybierz gemini", 0.0)

        counter = await self._get_today_counter(user.id, db)
        total_cost = float(counter.total_cost_usd if counter else Decimal("0"))
        budget_remaining = max(float(limits["daily_usd_cap"]) - total_cost, 0.0)

        if user.subscription_tier == "free" and provider_name == "grok":
            used = counter.grok_calls if counter else 0
            if used >= settings.DEMO_GROK_DAILY:
                return PolicyResult(
                    False, "Przekroczono limit", "Spróbuj providera gemini", budget_remaining
                )

        if user.subscription_tier == "free" and not limits["smart_unlimited"]:
            if (counter.smart_credits_used if counter else 0) >= settings.DEMO_SMART_CREDITS_DAILY:
                return PolicyResult(
                    False, "Przekroczono limit", "Przełącz na tryb eco", budget_remaining
                )

        if limits["gpt_daily"] is not None and provider_name == "openai":
            used_openai = await self._get_provider_usage_today(user.id, "openai", db)
            if used_openai >= int(limits["gpt_daily"]):
                return PolicyResult(False, "Przekroczono limit", "Wróć jutro po nowy limit", 0.0)

        if budget_remaining <= 0:
            return PolicyResult(False, "Przekroczono limit", "Spróbuj jutro", 0.0)

        return PolicyResult(True, None, None, budget_remaining)

    def check_command(self, user: User, command: str) -> bool:
        if user.subscription_tier == "unlimited" and command == "/github":
            return True
        blocked = self.BLOCKED_COMMANDS.get(user.role, [])
        return command not in blocked

    def get_provider_chain(self, user: User, profile: str) -> list[str]:
        _ = profile
        limits = self.get_effective_limits(user)
        chain = ["gemini", "deepseek", "groq", "openrouter", "grok", "openai", "anthropic"]
        return [provider for provider in chain if provider in limits["allowed_providers"]]

    def get_effective_limits(self, user: User) -> dict[str, Any]:
        role_access = self.PROVIDER_ACCESS.get(user.role, {})
        allowed_providers = set(role_access.keys())
        role_daily_cap = 5.0 if user.role == UserRole.FULL_ACCESS else 5.0
        limits: dict[str, Any] = {
            "allowed_providers": allowed_providers,
            "smart_unlimited": False,
            "gpt_daily": None,
            "daily_usd_cap": role_daily_cap,
            "github": user.role == UserRole.FULL_ACCESS,
        }

        subscription_tier = (
            user.subscription_tier if user.subscription_tier in self.SUBSCRIPTION_LIMITS else "free"
        )
        if subscription_tier == "free":
            limits["allowed_providers"] = set(self.PROVIDER_ACCESS[UserRole.DEMO].keys())
            limits["github"] = False
            return limits

        subscription_limits = self.SUBSCRIPTION_LIMITS[subscription_tier]
        if subscription_limits.get("all_providers"):
            limits["allowed_providers"] = {
                "gemini",
                "deepseek",
                "groq",
                "openrouter",
                "grok",
                "openai",
                "anthropic",
            }
        if subscription_limits.get("allowed_providers"):
            limits["allowed_providers"] |= set(subscription_limits["allowed_providers"])

        if subscription_limits.get("smart_unlimited"):
            limits["smart_unlimited"] = True

        if subscription_limits.get("gpt_daily") is not None:
            limits["gpt_daily"] = int(subscription_limits["gpt_daily"])

        sub_cap = subscription_limits.get("daily_usd_cap")
        if sub_cap is not None:
            limits["daily_usd_cap"] = max(float(sub_cap), float(limits["daily_usd_cap"]))

        if subscription_limits.get("github"):
            limits["github"] = True

        return limits

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
        limits = self.get_effective_limits(user)
        smart_remaining = (
            999999
            if limits["smart_unlimited"]
            else max(settings.DEMO_SMART_CREDITS_DAILY - used_credits, 0)
        )
        return {
            "grok_remaining": max(settings.DEMO_GROK_DAILY - used_grok, 0),
            "smart_credits_remaining": smart_remaining,
            "daily_budget_remaining": max(float(limits["daily_usd_cap"]) - used_cost, 0.0),
        }

    async def _get_provider_usage_today(self, user_id: Any, provider: str, db: AsyncSession) -> int:
        utc_now = datetime.now(timezone.utc)
        start = datetime.combine(utc_now.date(), time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        result = await db.execute(
            select(func.count(UsageLedger.id)).where(
                UsageLedger.user_id == user_id,
                UsageLedger.provider == provider,
                UsageLedger.created_at >= start,
                UsageLedger.created_at < end,
            )
        )
        return int(result.scalar() or 0)

    async def _get_today_counter(self, user_id: Any, db: AsyncSession) -> ToolCounter | None:
        result = await db.execute(
            select(ToolCounter).where(
                ToolCounter.user_id == user_id, ToolCounter.date == date.today()
            )
        )
        return result.scalar_one_or_none()


policy_engine = PolicyEngine()
