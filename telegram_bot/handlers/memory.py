from __future__ import annotations

from middleware.auth import with_auth_retry


async def handle_memory(update, context):
    await update.message.reply_text(f"🧠 Sesja: {context.user_data.get('conv_id')}")


async def handle_forget(update, context):
    context.user_data["conv_id"] = None
    await update.message.reply_text("✨ Zapomniano.")


async def handle_new_conversation(update, context):
    await handle_forget(update, context)


async def handle_export(update, context):
    chat_svc, auth_svc = context.bot_data["chat_service"], context.bot_data["auth_service"]
    cid = context.user_data.get("conv_id")
    if not cid:
        return await update.message.reply_text("Brak aktywnej rozmowy.")
    await with_auth_retry(lambda uid, tok: chat_svc.export_conversation(tok, cid), update, context, auth_svc)
    await update.message.reply_text("🚧 Eksport rozmowy...")
