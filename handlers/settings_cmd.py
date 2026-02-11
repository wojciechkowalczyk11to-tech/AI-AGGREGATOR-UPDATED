from __future__ import annotations
from keyboards.settings_keyboard import get_settings_keyboard
from middleware.auth import with_auth_retry
async def handle(update, context):
    auth_svc = context.bot_data["auth_service"]
    data = await with_auth_retry(lambda uid, tok: auth_svc.get_me(tok), update, context, auth_svc)
    await update.message.reply_text(f"⚙️ Ustawienia\nModel: {data.get('settings', {}).get('preferred_model')}", reply_markup=get_settings_keyboard(data.get("settings", {})))
