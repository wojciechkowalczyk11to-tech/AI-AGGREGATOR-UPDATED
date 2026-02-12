from __future__ import annotations
from services.base import BaseService
class AdminService(BaseService):
    async def get_system_overview(self, token: str) -> dict:
        return await self._request("GET", "/api/admin/stats/overview", token=token)
    async def list_users(self, token: str, limit: int = 100) -> list:
        return await self._request("GET", f"/api/admin/users?limit={limit}", token=token)
