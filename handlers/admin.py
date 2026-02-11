from __future__ import annotations
from middleware.auth import with_auth_retry
async def handle(update, context):
    if update.effective_user.id not in context.bot_data["settings"].admin_user_ids: return
    adm_svc, auth_svc = context.bot_data["admin_service"], context.bot_data["auth_service"]
    res = await with_auth_retry(lambda uid, tok: adm_svc.get_system_overview(tok), update, context, auth_svc)
    await update.message.reply_text(f"👑 Admin: {res.get('total_users')} użytkowników")
