from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from handlers import payments
from services.backend_client import BackendClient


class DummyMessage:
    def __init__(self) -> None:
        self.reply_text = AsyncMock()
        self.chat_id = 777
        self.successful_payment = None


@pytest.mark.asyncio
async def test_subscribe_shows_plans(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(payments, "access_gate", AsyncMock(return_value=True))
    backend = BackendClient("http://b")
    backend.get_plans = AsyncMock(
        return_value=[{"id": "pro", "label": "PRO", "stars": 99}]
    )
    message = DummyMessage()
    update = SimpleNamespace(effective_message=message)
    context = SimpleNamespace(
        user_data={"is_authorized": True}, bot_data={"backend_client": backend}
    )

    await payments.handle_subscribe(update, context)

    message.reply_text.assert_awaited_once()
    kwargs = message.reply_text.await_args.kwargs
    assert kwargs["reply_markup"].inline_keyboard[0][0].callback_data == "buy:pro"


@pytest.mark.asyncio
async def test_successful_payment_activates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(payments, "access_gate", AsyncMock(return_value=True))
    backend = BackendClient("http://b")
    backend.confirm_payment = AsyncMock(
        return_value={"plan": "PRO", "expires_at": "2026-01-01"}
    )
    payment = SimpleNamespace(
        invoice_payload="pro", total_amount=99, telegram_payment_charge_id="charge_1"
    )
    message = DummyMessage()
    message.successful_payment = payment
    update = SimpleNamespace(
        effective_message=message, effective_user=SimpleNamespace(id=1)
    )
    context = SimpleNamespace(
        user_data={"is_authorized": True, "backend_token": "tok"},
        bot_data={"backend_client": backend},
    )

    await payments.handle_successful_payment(update, context)

    backend.confirm_payment.assert_awaited_once_with("tok", "pro", 99, "charge_1")
    message.reply_text.assert_awaited_once_with("✅ Plan PRO aktywowany do 2026-01-01!")


@pytest.mark.asyncio
async def test_subscribe_denied_for_unauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(payments, "access_gate", AsyncMock(return_value=True))
    backend = BackendClient("http://b")
    backend.get_plans = AsyncMock()
    message = DummyMessage()
    update = SimpleNamespace(effective_message=message)
    context = SimpleNamespace(
        user_data={"is_authorized": False}, bot_data={"backend_client": backend}
    )

    await payments.handle_subscribe(update, context)

    message.reply_text.assert_awaited_once_with("Brak dostępu. Użyj /unlock <kod>")
    backend.get_plans.assert_not_called()
