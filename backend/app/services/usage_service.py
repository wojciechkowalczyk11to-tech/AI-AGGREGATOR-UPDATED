from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import JarvisBaseError
from app.db.models import UsageLedger


class UsageService:
    async def log_request(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID | None,
        provider: str,
        model: str,
        profile: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: int,
        fallback_used: bool,
    ) -> UsageLedger:
        try:
            ledger = UsageLedger(
                user_id=user_id,
                session_id=session_id,
                provider=provider,
                model=model,
                profile=profile,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=Decimal(str(cost_usd)),
                latency_ms=latency_ms,
                fallback_used=fallback_used,
            )
            db.add(ledger)
            await db.commit()
            await db.refresh(ledger)
            return ledger
        except Exception as exc:
            await db.rollback()
            raise JarvisBaseError("Nie udało się zapisać użycia", 500) from exc

    async def get_daily_cost(self, user_id: uuid.UUID, db: AsyncSession) -> float:
        start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            result = await db.execute(
                select(func.coalesce(func.sum(UsageLedger.cost_usd), 0)).where(
                    UsageLedger.user_id == user_id,
                    UsageLedger.created_at >= start,
                )
            )
            return float(result.scalar_one() or 0)
        except Exception as exc:
            raise JarvisBaseError("Nie udało się pobrać kosztu dziennego", 500) from exc

    async def get_usage_summary(
        self, user_id: uuid.UUID, days: int, db: AsyncSession
    ) -> dict[str, Any]:
        threshold = datetime.now(tz=timezone.utc) - timedelta(days=days)
        try:
            result = await db.execute(
                select(UsageLedger).where(
                    UsageLedger.user_id == user_id,
                    UsageLedger.created_at >= threshold,
                )
            )
            items = result.scalars().all()
            total_cost = float(sum(float(item.cost_usd) for item in items))
            total_input = sum(item.input_tokens for item in items)
            total_output = sum(item.output_tokens for item in items)

            by_provider: dict[str, dict[str, float | int]] = {}
            for item in items:
                bucket = by_provider.setdefault(
                    item.provider,
                    {"requests": 0, "cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0},
                )
                bucket["requests"] = int(bucket["requests"]) + 1
                bucket["cost_usd"] = float(bucket["cost_usd"]) + float(item.cost_usd)
                bucket["input_tokens"] = int(bucket["input_tokens"]) + item.input_tokens
                bucket["output_tokens"] = int(bucket["output_tokens"]) + item.output_tokens

            return {
                "days": days,
                "total_requests": len(items),
                "total_cost_usd": total_cost,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "by_provider": by_provider,
            }
        except Exception as exc:
            raise JarvisBaseError("Nie udało się pobrać podsumowania użycia", 500) from exc


usage_service = UsageService()
