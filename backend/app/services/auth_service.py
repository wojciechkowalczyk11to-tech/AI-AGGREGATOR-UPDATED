from __future__ import annotations

import uuid
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import JarvisBaseError, RateLimitExceededError
from app.core.security import create_access_token
from app.db.models import User, UserRole


class AuthService:
    async def register(self, telegram_id: int, db: AsyncSession) -> dict[str, Any]:
        try:
            result = await db.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if user is None:
                user = User(telegram_id=telegram_id, role=UserRole.DEMO, authorized=False)
                db.add(user)
                await db.commit()
                await db.refresh(user)

            token = create_access_token(
                {
                    "sub": str(user.id),
                    "tid": user.telegram_id,
                    "role": user.role.value,
                }
            )
            return {
                "id": str(user.id),
                "telegram_id": user.telegram_id,
                "role": user.role.value,
                "authorized": user.authorized,
                "access_token": token,
            }
        except JarvisBaseError:
            raise
        except Exception as exc:
            await db.rollback()
            raise JarvisBaseError("Nie udało się zarejestrować użytkownika", 500) from exc

    async def unlock(
        self,
        telegram_id: int,
        code: str,
        db: AsyncSession,
        redis: Redis | None,
    ) -> dict[str, Any]:
        settings = get_settings()
        try:
            if redis is not None:
                key = f"unlock_attempts:{telegram_id}"
                attempts = await redis.incr(key)
                if attempts == 1:
                    await redis.expire(key, 600)
                if attempts > 5:
                    raise RateLimitExceededError("Przekroczono limit prób odblokowania")

            result = await db.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if user is None:
                return {"success": False, "role": UserRole.DEMO.value}

            if code != settings.DEMO_UNLOCK_CODE:
                return {"success": False, "role": user.role.value}

            user.authorized = True
            await db.commit()
            await db.refresh(user)
            return {"success": True, "role": user.role.value}
        except RateLimitExceededError:
            raise
        except Exception as exc:
            await db.rollback()
            raise JarvisBaseError("Nie udało się odblokować użytkownika", 500) from exc

    async def bootstrap(self, telegram_id: int, code: str, db: AsyncSession) -> dict[str, Any]:
        settings = get_settings()
        try:
            if code != settings.BOOTSTRAP_ADMIN_CODE:
                return {"success": False}

            result = await db.execute(
                select(func.count()).select_from(User).where(User.role == UserRole.FULL_ACCESS)
            )
            full_users = int(result.scalar_one())
            if full_users > 0:
                return {"success": False}

            existing = await db.execute(select(User).where(User.telegram_id == telegram_id))
            user = existing.scalar_one_or_none()
            if user is None:
                user = User(telegram_id=telegram_id)
                db.add(user)

            user.role = UserRole.FULL_ACCESS
            user.authorized = True
            await db.commit()
            return {"success": True}
        except Exception as exc:
            await db.rollback()
            raise JarvisBaseError("Nie udało się wykonać bootstrap", 500) from exc

    async def get_me(self, user_id: uuid.UUID, db: AsyncSession) -> dict[str, Any]:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is None:
                raise JarvisBaseError("Użytkownik nie istnieje", 404)

            return {
                "id": str(user.id),
                "telegram_id": user.telegram_id,
                "role": user.role.value,
                "authorized": user.authorized,
                "verified": user.verified,
                "default_mode": user.default_mode,
                "settings": user.settings_,
            }
        except JarvisBaseError:
            raise
        except Exception as exc:
            raise JarvisBaseError("Nie udało się pobrać danych użytkownika", 500) from exc

    async def update_settings(
        self,
        user_id: uuid.UUID,
        settings_dict: dict[str, Any],
        db: AsyncSession,
    ) -> dict[str, Any]:
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is None:
                raise JarvisBaseError("Użytkownik nie istnieje", 404)

            merged = dict(user.settings_ or {})
            merged.update(settings_dict)
            user.settings_ = merged
            await db.commit()
            await db.refresh(user)
            return {"settings": user.settings_}
        except JarvisBaseError:
            raise
        except Exception as exc:
            await db.rollback()
            raise JarvisBaseError("Nie udało się zapisać ustawień", 500) from exc


auth_service = AuthService()
