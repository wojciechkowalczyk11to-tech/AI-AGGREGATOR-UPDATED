from __future__ import annotations
import pytest, os
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("BACKEND_URL", "http://b")
    monkeypatch.setenv("ALLOWED_USER_IDS", "[123]")
