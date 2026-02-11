from __future__ import annotations
import logging
async def handle_error(update, context):
    logging.error(f"Error: {context.error}")
    if update and hasattr(update, "effective_message") and update.effective_message:
        await update.effective_message.reply_text("⚠️ Błąd wewnętrzny.")
