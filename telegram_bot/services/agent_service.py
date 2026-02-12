from __future__ import annotations
from services.base import BaseService
class AgentService(BaseService):
    async def create_task(self, token: str, repo: str, desc: str, model: str = "gemini") -> dict:
        return await self._request("POST", "/api/agent/task", token=token, json={"repo_name": repo, "description": desc, "model": model})
