from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from middleware.access_control import access_gate

VALID_MODES = {"eco", "smart", "deep"}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await access_gate(update, context):
        return

    message = update.effective_message
    if message is None:
        return

    if not context.user_data.get("is_authorized", False):
        await message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    if not context.args:
        await message.reply_text("Użycie: /mode <eco|smart|deep>")
        return

    mode = context.args[0].lower()
    if mode not in VALID_MODES:
        await message.reply_text("Nieprawidłowy tryb. Użyj: eco, smart lub deep.")
        return

    context.user_data["mode"] = mode
    await message.reply_text(f"Tryb zmieniony na {mode}.")
