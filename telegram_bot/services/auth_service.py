from __future__ import annotations
from typing import Any
from services.base import BaseService
class AuthService(BaseService):
    async def register(self, telegram_chat_id: int, settings: dict | None = None) -> dict:
        return await self._request("POST", "/api/users/register", json={"telegram_chat_id": telegram_chat_id, "settings": settings or {}})
    async def update_settings(self, user_id: str, token: str, settings: dict) -> dict:
        return await self._request("PUT", f"/api/users/{user_id}/settings", token=token, json={"settings": settings})
    async def get_me(self, token: str) -> dict:
        return await self._request("GET", "/api/users/me", token=token)
