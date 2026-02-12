from __future__ import annotations

from config import BotSettings


def test_config():
    s = BotSettings(telegram_bot_token="t", allowed_user_ids=[1])
    assert s.telegram_bot_token == "t"
