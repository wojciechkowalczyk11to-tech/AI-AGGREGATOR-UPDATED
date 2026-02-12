from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UsageLedger, User, UserRole


class AdminService:
    async def get_overview(self, db: AsyncSession) -> dict[str, Any]:
        today = datetime.now(timezone.utc).date()

        total_users = await db.scalar(select(func.count(User.id)))
        active_today = await db.scalar(select(func.count(User.id)).where(func.date(User.last_seen_at) == today))
        total_cost_today = await db.scalar(
            select(func.coalesce(func.sum(UsageLedger.cost_usd), 0)).where(func.date(UsageLedger.created_at) == today)
        )
        providers_result = await db.execute(select(UsageLedger.provider).distinct())
        providers_available = sorted(
            {provider for provider in providers_result.scalars().all() if isinstance(provider, str) and provider}
        )

        return {
            "total_users": int(total_users or 0),
            "active_today": int(active_today or 0),
            "total_cost_today": float(total_cost_today or Decimal("0")),
            "providers_available": providers_available,
        }

    async def list_users(self, db: AsyncSession, limit: int = 50) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        result = await db.execute(select(User).order_by(User.created_at.desc()).limit(safe_limit))
        users = result.scalars().all()

        def to_iso(dt: datetime | None) -> str | None:
            if dt is None:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()

        return [
            {
                "telegram_id": user.telegram_id,
                "role": user.role.value,
                "authorized": user.authorized,
                "verified": user.verified,
                "subscription_tier": user.subscription_tier,
                "created_at": to_iso(user.created_at),
                "last_seen_at": to_iso(user.last_seen_at),
            }
            for user in users
        ]

    async def add_user(self, telegram_id: int, role: str, db: AsyncSession) -> dict[str, Any]:
        role_enum = self._parse_role(role)
        user = await self._get_user_by_telegram_id(telegram_id, db)
        if user is None:
            user = User(
                telegram_id=telegram_id,
                role=role_enum,
                authorized=True,
                verified=(role_enum == UserRole.FULL_ACCESS),
            )
            db.add(user)
        else:
            user.role = role_enum
            user.authorized = True
            if role_enum == UserRole.FULL_ACCESS:
                user.verified = True

        await db.commit()
        await db.refresh(user)
        return {"telegram_id": user.telegram_id, "role": user.role.value}

    async def change_role(self, telegram_id: int, new_role: str, db: AsyncSession) -> dict[str, Any]:
        role_enum = self._parse_role(new_role)
        user = await self._get_user_by_telegram_id(telegram_id, db)
        if user is None:
            raise ValueError("Użytkownik nie istnieje.")

        user.role = role_enum
        if role_enum == UserRole.FULL_ACCESS:
            user.authorized = True
            user.verified = True

        await db.commit()
        await db.refresh(user)
        return {"telegram_id": user.telegram_id, "role": user.role.value}

    async def remove_user(self, telegram_id: int, db: AsyncSession) -> bool:
        user = await self._get_user_by_telegram_id(telegram_id, db)
        if user is None:
            return False

        await db.delete(user)
        await db.commit()
        return True

    @staticmethod
    def _parse_role(role: str) -> UserRole:
        normalized = role.strip().upper()
        try:
            return UserRole[normalized]
        except KeyError as exc:
            raise ValueError("Nieprawidłowa rola użytkownika.") from exc

    @staticmethod
    async def _get_user_by_telegram_id(telegram_id: int, db: AsyncSession) -> User | None:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()


admin_service = AdminService()
