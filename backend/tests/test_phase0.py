import json

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.core.exceptions import JarvisBaseError, PolicyDeniedError, RateLimitExceededError
from app.core.logging_config import JSONFormatter
from app.core.security import create_access_token, verify_token
from app.db.models.user import User, UserRole


class TestConfig:
    def test_settings_loads(self) -> None:
        settings = get_settings()
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.DEMO_GROK_DAILY == 5
        assert settings.LOG_LEVEL == "INFO"

    def test_feature_flags_have_defaults(self) -> None:
        settings = get_settings()
        assert isinstance(settings.VOICE_ENABLED, bool)
        assert isinstance(settings.PAYMENTS_ENABLED, bool)

    def test_telegram_ids_parse(self) -> None:
        settings = get_settings()
        ids = [int(x.strip()) for x in settings.FULL_TELEGRAM_IDS.split(",") if x.strip()]
        assert len(ids) >= 1


class TestExceptions:
    def test_jarvis_base_error(self) -> None:
        err = JarvisBaseError(detail="test", status_code=500)
        assert err.detail == "test"
        assert err.status_code == 500

    def test_policy_denied(self) -> None:
        err = PolicyDeniedError("Brak dostępu")
        assert err.status_code == 403

    def test_rate_limit(self) -> None:
        err = RateLimitExceededError()
        assert err.status_code == 429


class TestSecurity:
    def test_create_and_verify_token(self) -> None:
        token = create_access_token({"sub": "123456", "role": "DEMO"})
        payload = verify_token(token)
        assert payload["sub"] == "123456"
        assert payload["role"] == "DEMO"

    def test_verify_invalid_token_raises(self) -> None:
        with pytest.raises(Exception):
            verify_token("invalid.token.here")


class TestLogging:
    def test_json_formatter(self) -> None:
        import logging

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "hello"
        assert parsed["level"] == "INFO"
        assert "timestamp" in parsed


class TestUserModel:
    @pytest.mark.asyncio
    async def test_create_user(self, test_session) -> None:
        user = User(telegram_id=999999, role=UserRole.DEMO)
        test_session.add(user)
        await test_session.commit()

        result = await test_session.execute(select(User).where(User.telegram_id == 999999))
        found = result.scalar_one()
        assert found.role == UserRole.DEMO
        assert found.authorized is False
        assert found.verified is False
        assert found.default_mode == "eco"
        assert found.subscription_tier == "free"
        assert found.id is not None

    @pytest.mark.asyncio
    async def test_create_full_access_user(self, test_session) -> None:
        user = User(telegram_id=888888, role=UserRole.FULL_ACCESS, authorized=True)
        test_session.add(user)
        await test_session.commit()

        result = await test_session.execute(select(User).where(User.telegram_id == 888888))
        found = result.scalar_one()
        assert found.role == UserRole.FULL_ACCESS
        assert found.authorized is True
