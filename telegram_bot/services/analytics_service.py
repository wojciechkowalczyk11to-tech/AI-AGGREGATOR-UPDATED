from __future__ import annotations
from services.base import BaseService
class AnalyticsService(BaseService):
    async def get_usage_stats(self, token: str, days: int = 30) -> dict:
        return await self._request("GET", f"/api/analytics/usage?days={days}", token=token)
