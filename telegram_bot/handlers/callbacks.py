from __future__ import annotations

from keyboards.model_selector import get_model_selector_keyboard
from middleware.auth import with_auth_retry


async def handle(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    auth_svc = context.bot_data["auth_service"]

    if data.startswith("set_model:"):
        p = data.split(":")[1]
        await with_auth_retry(
            lambda uid, tok: auth_svc.update_settings(uid, tok, {"preferred_model": p}),
            update,
            context,
            auth_svc,
        )
        await query.edit_message_text(f"✅ Model: {p}")
    elif data == "menu:models":
        chat_svc = context.bot_data["chat_service"]
        providers = await chat_svc.get_providers()
        await query.edit_message_text(
            "🤖 Wybierz model:",
            reply_markup=get_model_selector_keyboard(providers=providers),
        )
    elif data == "confirm:forget":
        context.user_data["conv_id"] = None
        await query.edit_message_text("✨ Wyczyszczono.")
