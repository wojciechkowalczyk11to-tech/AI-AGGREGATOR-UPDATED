from __future__ import annotations

from config import BotSettings
from services.backend_client import BackendClient
from telegram import Update
from telegram.ext import ContextTypes


async def access_gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if user is None:
        return False

    backend_client = context.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        return False

    telegram_id = user.id
    if "backend_token" not in context.user_data:
        registration = await backend_client.register(telegram_id)
        token = registration.get("access_token") or registration.get("token")
        if isinstance(token, str) and token:
            context.user_data["backend_token"] = token
        context.user_data["is_authorized"] = bool(registration.get("authorized", False))
        context.user_data["user_role"] = registration.get("role", "DEMO")
        context.user_data["_just_registered"] = True
    else:
        context.user_data["_just_registered"] = False

    return True


def is_admin(telegram_id: int, settings: BotSettings) -> bool:
    return telegram_id in settings.admin_user_ids
