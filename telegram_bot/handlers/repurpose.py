from __future__ import annotations
from middleware.auth import with_auth_retry
async def handle(update, context):
    txt = " ".join(context.args) if context.args else (update.message.reply_to_message.text if update.message.reply_to_message else "")
    if not txt: return await update.message.reply_text("Daj tekst.")
    chat_svc, auth_svc = context.bot_data["chat_service"], context.bot_data["auth_service"]
    res = await with_auth_retry(lambda uid, tok: chat_svc.send_message(uid, tok, f"Repurpose this: {txt}"), update, context, auth_svc)
    await update.message.reply_text(res.get("response", ""))
