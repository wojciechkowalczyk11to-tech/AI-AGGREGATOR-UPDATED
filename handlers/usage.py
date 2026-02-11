from __future__ import annotations
from middleware.auth import with_auth_retry
async def handle(update, context):
    an_svc, auth_svc = context.bot_data["analytics_service"], context.bot_data["auth_service"]
    res = await with_auth_retry(lambda uid, tok: an_svc.get_usage_stats(tok), update, context, auth_svc)
    await update.message.reply_text(f"📊 Zużycie: ${res.get('totals',{}).get('cost_usd',0):.4f}")
