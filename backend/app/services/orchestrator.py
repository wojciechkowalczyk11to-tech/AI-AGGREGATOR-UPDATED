from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import JarvisBaseError, PolicyDeniedError, ProviderError
from app.db.models import ChatSession, Message, User
from app.providers.factory import ProviderFactory
from app.services.policy_engine import PolicyEngine, policy_engine
from app.services.usage_service import UsageService, usage_service


class Orchestrator:
    def __init__(
        self,
        policy_engine_instance: PolicyEngine,
        provider_factory: ProviderFactory,
        usage_service_instance: UsageService,
    ) -> None:
        self._policy_engine = policy_engine_instance
        self._provider_factory = provider_factory
        self._usage_service = usage_service_instance

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
        access = await self._policy_engine.check_access(
            user, provider_pref or "gemini", db, settings
        )
        if not access.allowed:
            raise PolicyDeniedError(access.denied_reason or "Brak dostępu")

        session = await self._get_or_create_session(user, session_id, mode, provider_pref, db)
        history = await self._get_history(session.id, db)
        messages = history + [{"role": "user", "content": prompt}]

        selected_provider = (provider_pref or "gemini").lower()
        provider = self._provider_factory.get(selected_provider)
        if provider is None:
            raise ProviderError("Provider jest niedostępny")

        provider_result = await provider.generate(
            messages=messages,
            profile=mode,
            max_tokens=1200,
            temperature=0.7,
        )

        await self._usage_service.log_request(
            db=db,
            user_id=user.id,
            session_id=session.id,
            provider=provider_result.provider,
            model=provider_result.model,
            profile=mode,
            input_tokens=provider_result.input_tokens,
            output_tokens=provider_result.output_tokens,
            cost_usd=provider_result.cost_usd,
            latency_ms=provider_result.latency_ms,
            fallback_used=provider_result.fallback_used,
        )

        smart_credits = 1 if mode in {"smart", "deep"} else 0
        await self._policy_engine.increment_counters(
            user=user,
            provider=provider_result.provider,
            cost=provider_result.cost_usd,
            smart_credits=smart_credits,
            db=db,
        )

        await self._save_messages(session=session, prompt=prompt, reply=provider_result.text, db=db)

        return {
            "response": provider_result.text,
            "meta": {
                "model": provider_result.model,
                "provider": provider_result.provider,
                "cost_usd": provider_result.cost_usd,
                "input_tokens": provider_result.input_tokens,
                "output_tokens": provider_result.output_tokens,
                "latency_ms": provider_result.latency_ms,
                "fallback_used": provider_result.fallback_used,
            },
            "session_id": str(session.id),
        }

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
                    select(ChatSession).where(
                        ChatSession.id == session_id, ChatSession.user_id == user.id
                    )
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
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at.desc())
                .limit(10)
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
