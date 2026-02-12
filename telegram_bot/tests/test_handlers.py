from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from handlers.start import handle
from services.backend_client import BackendClient


@pytest.mark.asyncio
async def test_start():
    u, c = MagicMock(), MagicMock()
    u.effective_user.id = 123
    u.effective_message = AsyncMock()

    class MockBackendClient(BackendClient):
        def __init__(self):
            pass

    backend_client = MockBackendClient()
    c.bot_data = {"backend_client": backend_client}
    c.user_data = {"backend_token": "test-token"}

    await handle(u, c)
    u.effective_message.reply_text.assert_called_once()
