from __future__ import annotations

import pytest
import respx
from httpx import Response

from services.backend_client import BackendClient


@pytest.mark.asyncio
async def test_register_success() -> None:
    async with respx.mock:
        route = respx.post("http://b/api/v1/auth/register").mock(
            return_value=Response(
                200, json={"access_token": "tok", "authorized": False}
            )
        )
        client = BackendClient("http://b")
        result = await client.register(123)
        await client.close()

    assert route.called
    assert result["access_token"] == "tok"


@pytest.mark.asyncio
async def test_chat_success() -> None:
    async with respx.mock:
        route = respx.post("http://b/api/v1/chat/").mock(
            return_value=Response(
                200, json={"response": "ok", "model": "gpt", "cost": 0.1}
            )
        )
        client = BackendClient("http://b")
        result = await client.chat("tok", "hej", None, None, "smart")
        await client.close()

    assert route.called
    assert result["response"] == "ok"


@pytest.mark.asyncio
async def test_chat_backend_down_graceful() -> None:
    async with respx.mock:
        respx.post("http://b/api/v1/chat/").mock(side_effect=RuntimeError("down"))
        client = BackendClient("http://b")
        result = await client.chat("tok", "hej", None, None, "smart")
        await client.close()

    assert result["ok"] is False
    assert "niedostępny" in result["error"].lower()
