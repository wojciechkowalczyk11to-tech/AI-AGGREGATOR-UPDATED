from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import InviteCode, User, UserRole


class InviteService:
    async def create_invite(
        self,
        admin_tid: int,
        role: str,
        ttl_hours: int,
        max_uses: int,
        db: AsyncSession,
    ) -> str:
        if ttl_hours <= 0:
            raise ValueError("Czas ważności musi być większy od zera.")
        if max_uses <= 0:
            raise ValueError("Liczba użyć musi być większa od zera.")

        role_enum = self._parse_role(role)
        code = secrets.token_urlsafe(24)[:32]
        invite = InviteCode(
            code_hash=self._hash_code(code),
            role=role_enum,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
            uses_left=max_uses,
            created_by=admin_tid,
        )
        db.add(invite)
        await db.commit()
        return code

    async def validate_invite(self, code: str, db: AsyncSession) -> str | None:
        invite = await self._get_active_invite(code, db)
        if invite is None:
            return None
        return invite.role.value

    async def consume_invite(self, code: str, telegram_id: int, db: AsyncSession) -> dict[str, Any]:
        invite = await self._get_active_invite(code, db)
        if invite is None:
            return {"success": False, "role": None}

        invite.uses_left -= 1
        invite.consumed_by = telegram_id
        invite.consumed_at = datetime.now(timezone.utc)

        user_result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(
                telegram_id=telegram_id,
                role=invite.role,
                authorized=True,
                verified=(invite.role == UserRole.FULL_ACCESS),
            )
            db.add(user)
        elif invite.role == UserRole.FULL_ACCESS and user.role != UserRole.FULL_ACCESS:
            user.role = UserRole.FULL_ACCESS
            user.authorized = True
            user.verified = True

        await db.commit()
        return {"success": True, "role": invite.role.value}

    async def _get_active_invite(self, code: str, db: AsyncSession) -> InviteCode | None:
        code_hash = self._hash_code(code)
        result = await db.execute(select(InviteCode).where(InviteCode.code_hash == code_hash))
        invite = result.scalar_one_or_none()
        if invite is None:
            return None

        now = datetime.now(timezone.utc)
        expires_at = invite.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            return None
        if invite.uses_left <= 0:
            return None
        return invite

    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @staticmethod
    def _parse_role(role: str) -> UserRole:
        normalized = role.strip().upper()
        try:
            return UserRole[normalized]
        except KeyError as exc:
            raise ValueError("Nieprawidłowa rola zaproszenia.") from exc


invite_service = InviteService()
