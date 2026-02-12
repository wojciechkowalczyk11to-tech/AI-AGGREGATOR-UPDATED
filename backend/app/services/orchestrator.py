from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.circuit_breaker import CircuitBreaker
from app.core.config import get_settings
from app.core.exceptions import (
    AllProvidersFailedError,
    JarvisBaseError,
    PolicyDeniedError,
    ProviderError,
)
from app.db.models import ChatSession, Message, User, UserRole
from app.providers.base import ProviderResult
from app.providers.factory import ProviderFactory
from app.services.model_router import ModelRouter
from app.services.policy_engine import PolicyEngine, policy_engine
from app.services.usage_service import UsageService, usage_service


class Orchestrator:
    def __init__(
        self,
        policy_engine_instance: PolicyEngine,
        provider_factory: ProviderFactory,
        usage_service_instance: UsageService,
        model_router: ModelRouter | None = None,
    ) -> None:
        self._policy_engine = policy_engine_instance
        self._provider_factory = provider_factory
        self._usage_service = usage_service_instance
        self._model_router = model_router or ModelRouter()

    async def process_chat(
        self,
        user: User,
        prompt: str,
        session_id: uuid.UUID | None,
        provider_pref: str | None,
        mode: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        settings = get_settings()
        requested_provider = (provider_pref or "gemini").lower()
        access = await self._policy_engine.check_access(user, requested_provider, db, settings)
        if not access.allowed:
            raise PolicyDeniedError(access.denied_reason or "Brak dostępu")

        session = await self._get_or_create_session(user, session_id, mode, provider_pref, db)
        history = await self._get_history(session.id, db)
        messages = history + [{"role": "user", "content": prompt}]

        selected_mode = self._resolve_mode(user=user, prompt=prompt, mode=mode, budget=access.budget_remaining)
        selected_mode, routing_note = await self._apply_demo_credit_fallback(
            user=user,
            mode=selected_mode,
            db=db,
            settings=settings,
        )

        provider_result = await self._run_with_fallback_chain(
            user=user,
            provider_pref=provider_pref,
            mode=selected_mode,
            messages=messages,
        )

        smart_credits = 0
        if selected_mode in {"smart", "deep"}:
            smart_credits = self._model_router.calculate_smart_credits(
                provider_result.input_tokens,
                provider_result.output_tokens,
            )

        await self._usage_service.log_request(
            db=db,
            user_id=user.id,
            session_id=session.id,
            provider=provider_result.provider,
            model=provider_result.model,
            profile=selected_mode,
            input_tokens=provider_result.input_tokens,
            output_tokens=provider_result.output_tokens,
            cost_usd=provider_result.cost_usd,
            latency_ms=provider_result.latency_ms,
            fallback_used=provider_result.fallback_used,
        )

        await self._policy_engine.increment_counters(
            user=user,
            provider=provider_result.provider,
            cost=provider_result.cost_usd,
            smart_credits=smart_credits,
            db=db,
        )

        reply_text = provider_result.text
        if routing_note:
            reply_text = f"{routing_note}\n\n{reply_text}"

        await self._save_messages(session=session, prompt=prompt, reply=reply_text, db=db)

        return {
            "response": reply_text,
            "meta": {
                "model": provider_result.model,
                "provider": provider_result.provider,
                "cost_usd": provider_result.cost_usd,
                "input_tokens": provider_result.input_tokens,
                "output_tokens": provider_result.output_tokens,
                "latency_ms": provider_result.latency_ms,
                "fallback_used": provider_result.fallback_used,
                "profile": selected_mode,
            },
            "session_id": str(session.id),
        }

    async def _run_with_fallback_chain(
        self,
        user: User,
        provider_pref: str | None,
        mode: str,
        messages: list[dict[str, str]],
    ) -> ProviderResult:
        chain = (
            [provider_pref.lower()]
            if provider_pref
            else self._policy_engine.get_provider_chain(user=user, profile=mode)
        )
        errors: list[str] = []

        for provider_name in chain:
            provider = self._provider_factory.get(provider_name)
            if provider is None:
                errors.append(f"Provider {provider_name} jest niedostępny")
                continue

            breaker = CircuitBreaker(provider_name)
            if breaker.is_open():
                errors.append(f"Provider {provider_name} jest tymczasowo niedostępny")
                continue

            try:
                result = await provider.generate(
                    messages=messages,
                    profile=mode,
                    max_tokens=1200,
                    temperature=0.7,
                )
                breaker.record_success()
                if provider_name != chain[0]:
                    result.fallback_used = True
                return result
            except ProviderError as exc:
                breaker.record_failure()
                errors.append(exc.detail)

        raise AllProvidersFailedError("Wszyscy providerzy zawiedli. Spróbuj ponownie później. " + "; ".join(errors))

    async def _apply_demo_credit_fallback(
        self,
        user: User,
        mode: str,
        db: AsyncSession,
        settings: Any,
    ) -> tuple[str, str | None]:
        if user.role != UserRole.DEMO or mode not in {"smart", "deep"}:
            return mode, None

        remaining = await self._policy_engine.get_remaining_limits(user=user, db=db, settings=settings)
        if int(remaining["smart_credits_remaining"]) > 0:
            return mode, None
        return "eco", "⚠️ Kredyty SMART wyczerpane, użyto trybu ECO."

    def _resolve_mode(self, user: User, prompt: str, mode: str, budget: float) -> str:
        if mode.lower() != "auto":
            return mode.lower()
        difficulty = self._model_router.classify_difficulty(prompt)
        return self._model_router.select_profile(
            difficulty=difficulty,
            user_mode=mode,
            user_role=user.role.value,
            budget_remaining=budget,
        )

    async def _get_or_create_session(
        self,
        user: User,
        session_id: uuid.UUID | None,
        mode: str,
        provider_pref: str | None,
        db: AsyncSession,
    ) -> ChatSession:
        try:
            if session_id is not None:
                result = await db.execute(
                    select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
                )
                found = result.scalar_one_or_none()
                if found is not None:
                    return found

            session = ChatSession(
                user_id=user.id,
                mode=mode,
                provider_pref=provider_pref,
                last_active_at=datetime.now(tz=timezone.utc),
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
        except Exception as exc:
            await db.rollback()
            raise JarvisBaseError("Nie udało się utworzyć sesji", 500) from exc

    async def _get_history(self, session_id: uuid.UUID, db: AsyncSession) -> list[dict[str, str]]:
        try:
            result = await db.execute(
                select(Message).where(Message.session_id == session_id).order_by(Message.created_at.desc()).limit(10)
            )
            rows = list(reversed(result.scalars().all()))
            return [{"role": item.role, "content": item.content} for item in rows]
        except Exception as exc:
            raise JarvisBaseError("Nie udało się pobrać historii wiadomości", 500) from exc

    async def _save_messages(
        self,
        session: ChatSession,
        prompt: str,
        reply: str,
        db: AsyncSession,
    ) -> None:
        try:
            db.add(Message(session_id=session.id, role="user", content=prompt))
            db.add(Message(session_id=session.id, role="assistant", content=reply))
            session.message_count += 2
            session.last_active_at = datetime.now(tz=timezone.utc)
            await db.commit()
        except Exception as exc:
            await db.rollback()
            raise JarvisBaseError("Nie udało się zapisać wiadomości", 500) from exc


def build_orchestrator() -> Orchestrator:
    settings = get_settings()
    return Orchestrator(policy_engine, ProviderFactory(settings), usage_service)
