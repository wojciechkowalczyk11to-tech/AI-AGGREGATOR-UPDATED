from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock
from middleware.auth import ensure_authenticated
@pytest.mark.asyncio
async def test_auth_mw():
    update, context, auth = MagicMock(), MagicMock(), AsyncMock()
    context.user_data = {"backend_user_id":"u", "access_token":"t"}
    uid, tok = await ensure_authenticated(update, context, auth)
    assert uid == "u"
