from __future__ import annotations

from middleware.access_control import access_gate
from services.backend_client import BackendClient
from telegram import Update
from telegram.ext import ContextTypes


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await access_gate(update, context):
        return

    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    if not context.args:
        await message.reply_text("Użycie: /invite <kod>")
        return

    backend_client = context.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    code = context.args[0]
    validation = await backend_client.invite_validate(code)
    if validation.get("ok") is False or not validation.get("valid", False):
        await message.reply_text("Nieprawidłowy lub wygasły kod.")
        return

    consume_result = await backend_client.invite_consume(code, user.id)
    if consume_result.get("ok") is False or not consume_result.get("success", False):
        await message.reply_text("Nieprawidłowy lub wygasły kod.")
        return

    await message.reply_text(f"Zaproszenie przyjęte! Rola: {consume_result.get('role')}")
