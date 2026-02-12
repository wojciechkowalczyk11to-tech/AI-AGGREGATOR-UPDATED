from __future__ import annotations

from app.db.session import should_create_all


def test_should_create_all_for_sqlite_url(monkeypatch) -> None:
    monkeypatch.delenv("DB_CREATE_ALL", raising=False)
    assert should_create_all("sqlite+aiosqlite:///./test.db") is True


def test_should_create_all_for_postgres_url(monkeypatch) -> None:
    monkeypatch.delenv("DB_CREATE_ALL", raising=False)
    assert should_create_all("postgresql+asyncpg://user:pass@localhost:5432/db") is False


def test_should_create_all_for_postgres_url_with_override(monkeypatch) -> None:
    monkeypatch.setenv("DB_CREATE_ALL", "1")
    assert should_create_all("postgresql+asyncpg://user:pass@localhost:5432/db") is True
