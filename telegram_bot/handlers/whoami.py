from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from middleware.access_control import access_gate
from services.backend_client import BackendClient


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await access_gate(update, context):
        return

    message = update.effective_message
    if message is None:
        return

    if not context.user_data.get("is_authorized", False):
        await message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    backend_client = context.bot_data.get("backend_client")
    token = context.user_data.get("backend_token")
    if not isinstance(backend_client, BackendClient) or not isinstance(token, str):
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    me = await backend_client.get_me(token)
    if me.get("ok") is False:
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    role = str(me.get("role", "DEMO"))
    authorized = "tak" if bool(me.get("authorized", False)) else "nie"
    plan = str(me.get("subscription_tier", me.get("plan", "free")))
    default_mode = str(me.get("default_mode", "smart"))

    await message.reply_text(
        f"Rola: {role}\n"
        f"Autoryzacja: {authorized}\n"
        f"Plan: {plan}\n"
        f"Tryb domyślny: {default_mode}"
    )
