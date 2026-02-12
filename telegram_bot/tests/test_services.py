from __future__ import annotations

import pytest
import respx
from httpx import Response
from services.auth_service import AuthService


@pytest.mark.asyncio
async def test_auth():
    async with respx.mock:
        respx.post("http://b/api/users/register").mock(
            return_value=Response(200, json={"id": "u", "access_token": "t"})
        )
        s = AuthService("http://b")
        r = await s.register(1)
        assert r["id"] == "u"
