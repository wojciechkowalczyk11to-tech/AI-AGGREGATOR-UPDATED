from __future__ import annotations
import aiofiles
from services.base import BaseService
class RagService(BaseService):
    async def upload_file(self, token: str, filepath: str, filename: str) -> dict:
        async with aiofiles.open(filepath, "rb") as f:
            content = await f.read()
        return await self._request("POST", "/api/rag/upload", token=token, files={"file": (filename, content)})
    async def search(self, token: str, query: str, top_k: int = 5) -> dict:
        return await self._request("POST", "/api/rag/search", token=token, json={"query": query, "top_k": top_k})
    async def list_documents(self, token: str) -> list:
        return await self._request("GET", "/api/rag/documents", token=token)
    async def export_workspace(self, token: str) -> dict:
        return await self._request("GET", "/api/rag/workspace/export", token=token)
