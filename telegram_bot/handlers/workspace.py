from __future__ import annotations
from middleware.auth import with_auth_retry
import io
async def handle_list(update, context):
    rag_svc, auth_svc = context.bot_data["rag_service"], context.bot_data["auth_service"]
    docs = await with_auth_retry(lambda uid, tok: rag_svc.list_documents(tok), update, context, auth_svc)
    await update.message.reply_text("📂 Dokumenty:\n" + "\n".join([d["filename"] for d in docs]))
async def handle_download(update, context):
    rag_svc, auth_svc = context.bot_data["rag_service"], context.bot_data["auth_service"]
    res = await with_auth_retry(lambda uid, tok: rag_svc.export_workspace(tok), update, context, auth_svc)
    # Assume res contains file data or URL
    await update.message.reply_text("🚧 Pobieranie workspace...")
