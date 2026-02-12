from __future__ import annotations
from middleware.auth import with_auth_retry
async def handle_search(update, context):
    if not context.args: return
    rag_svc, auth_svc = context.bot_data["rag_service"], context.bot_data["auth_service"]
    res = await with_auth_retry(lambda uid, tok: rag_svc.search(tok, " ".join(context.args)), update, context, auth_svc)
    text = "🔍 Wyniki:\n" + "\n".join([r["content"][:200] for r in res.get("results", [])])
    await update.message.reply_text(text[:4000])
async def handle_upload_command(update, context):
    if update.message.reply_to_message and update.message.reply_to_message.document:
        orig = update.message; update.message = update.message.reply_to_message
        from handlers import documents; await documents.handle(update, context)
        update.message = orig
    else: await update.message.reply_text("Odpisz /upload na dokument.")
