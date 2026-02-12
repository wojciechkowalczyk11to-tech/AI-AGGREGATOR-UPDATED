from __future__ import annotations

from middleware.access_control import access_gate
from services.backend_client import BackendClient
from telegram import Update
from telegram.ext import ContextTypes


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await access_gate(update, context):
        return

    message = update.effective_message
    if message is None:
        return

    if not context.user_data.get("is_authorized", False):
        await message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    backend_client = context.bot_data.get("backend_client")
    token = context.user_data.get("backend_token")
    if not isinstance(backend_client, BackendClient) or not isinstance(token, str):
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    usage = await backend_client.get_usage(token, 30)
    limits = await backend_client.get_limits(token)
    if usage.get("ok") is False or limits.get("ok") is False:
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    daily_cost = float(usage.get("daily_cost", usage.get("today_cost", 0.0)))
    monthly_total = float(usage.get("monthly_total", usage.get("month_cost", 0.0)))
    remaining_requests = int(limits.get("remaining_requests", 0))
    remaining_budget = float(limits.get("remaining_budget", 0.0))

    await message.reply_text(
        "📊 Twoje użycie:\n"
        f"• Dzisiejszy koszt: ${daily_cost:.4f}\n"
        f"• Pozostałe zapytania: {remaining_requests}\n"
        f"• Pozostały budżet: ${remaining_budget:.4f}\n"
        f"• Suma w tym miesiącu: ${monthly_total:.4f}"
    )
