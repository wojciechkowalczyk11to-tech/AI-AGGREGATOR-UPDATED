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
        await message.reply_text("Użycie: /unlock <kod>")
        return

    code = context.args[0]
    backend_client = context.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    result = await backend_client.unlock(user.id, code)
    if result.get("ok") is False:
        status_code = int(result.get("status_code", 0))
        if status_code == 429:
            await message.reply_text("Za dużo prób. Spróbuj za 10 minut.")
            return
        await message.reply_text("Nieprawidłowy kod.")
        return

    role = str(result.get("role", "FULL_ACCESS"))
    context.user_data["is_authorized"] = True
    context.user_data["user_role"] = role
    await message.reply_text(f"Odblokowano dostęp! Twoja rola: {role}")
