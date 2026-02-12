from __future__ import annotations

import time

from services.base import BaseService


class ChatService(BaseService):
    async def send_message(
        self,
        user_id: str,
        token: str,
        prompt: str,
        conversation_id: str | None = None,
        use_rag: bool = False,
    ) -> dict:
        payload = {"user_id": user_id, "prompt": prompt, "use_rag": use_rag}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        start = time.monotonic()
        result = await self._request("POST", "/api/chat/", token=token, json=payload)
        result["_elapsed"] = time.monotonic() - start
        return result

    async def get_providers(self) -> list[str]:
        return await self._request("GET", "/api/chat/providers")

    async def send_with_provider(
        self,
        user_id: str,
        token: str,
        prompt: str,
        provider: str,
        conversation_id: str | None = None,
    ) -> dict:
        full_prompt = f"/{provider} {prompt}" if not prompt.startswith(f"/{provider}") else prompt
        return await self.send_message(user_id, token, full_prompt, conversation_id)

    async def transcribe(self, token: str, filepath: str) -> dict:
        import aiofiles

        async with aiofiles.open(filepath, "rb") as f:
            content = await f.read()
        return await self._request("POST", "/api/chat/stt", token=token, files={"file": ("voice.wav", content)})

    async def export_conversation(self, token: str, conversation_id: str) -> dict:
        return await self._request("GET", f"/api/chat/conversations/{conversation_id}/export", token=token)
