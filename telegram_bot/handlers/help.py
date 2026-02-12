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

    if not context.user_data.get("is_authorized", False):
        await message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    await message.reply_text(
        "Dostępne komendy:\n"
        "/start — uruchamia bota\n"
        "/help — pokazuje tę pomoc\n"
        "/unlock <kod> — odblokowuje konto\n"
        "/whoami — pokazuje dane konta\n"
        "/mode <eco|smart|deep> — zmienia tryb odpowiedzi\n"
        "/usage — pokazuje limity i użycie\n"
        "/subscribe — kup plan\n"
        "/plan — pokazuje aktywny plan"
    )
