from __future__ import annotations

from middleware.access_control import access_gate
from telegram import Update
from telegram.ext import ContextTypes


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await access_gate(update, context):
        return

    message = update.effective_message
    if message is None:
        return

    is_new = bool(context.user_data.get("_just_registered", False))
    if is_new:
        await message.reply_text(
            "Witaj! Aby odblokować dostęp, użyj komendy /unlock <kod>. "
            "Po odblokowaniu możesz użyć /help, aby zobaczyć komendy."
        )
        return

    await message.reply_text("Witaj ponownie! Użyj /help aby zobaczyć komendy.")
