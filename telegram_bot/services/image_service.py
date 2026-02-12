from __future__ import annotations
from services.base import BaseService
class ImageService(BaseService):
    async def generate_image(self, token: str, prompt: str) -> dict:
        return await self._request("POST", "/api/image/generate", token=token, json={"prompt": prompt})
