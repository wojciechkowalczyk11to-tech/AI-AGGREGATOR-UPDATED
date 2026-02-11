from __future__ import annotations
import tempfile, os
from middleware.auth import with_auth_retry
async def handle(update, context):
    doc = update.message.document
    rag_svc, auth_svc = context.bot_data["rag_service"], context.bot_data["auth_service"]
    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(doc.file_name)[1], delete=False) as tmp: tmp_path = tmp.name
    try:
        f = await context.bot.get_file(doc.file_id)
        await f.download_to_drive(tmp_path)
        await with_auth_retry(lambda uid, tok: rag_svc.upload_file(tok, tmp_path, doc.file_name), update, context, auth_svc)
        await update.message.reply_text(f"✅ Wgrano {doc.file_name}")
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)
