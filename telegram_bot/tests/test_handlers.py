from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from handlers.start import handle
@pytest.mark.asyncio
async def test_start():
    u, c = MagicMock(), MagicMock()
    u.message = AsyncMock()
    await handle(u, c)
    u.message.reply_text.assert_called_once()
