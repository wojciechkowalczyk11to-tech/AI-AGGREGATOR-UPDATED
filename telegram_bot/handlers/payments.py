from __future__ import annotations

from middleware.access_control import access_gate
from services.backend_client import BackendClient
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram.ext import ContextTypes


async def handle_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await access_gate(update, context):
        return

    message = update.effective_message
    if message is None:
        return

    if not context.user_data.get("is_authorized", False):
        await message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    backend_client = context.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    plans = await backend_client.get_plans()
    if not plans:
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{str(plan.get('label', plan.get('name', 'Plan')))} — ⭐ {int(plan.get('stars', 0))}",
                callback_data=f"buy:{str(plan.get('id', ''))}",
            )
        ]
        for plan in plans
        if str(plan.get("id", ""))
    ]

    if not keyboard:
        await message.reply_text("Brak dostępnych planów.")
        return

    context.bot_data["plans_cache"] = plans
    await message.reply_text("Wybierz plan subskrypcji:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return

    await query.answer()

    if not await access_gate(update, context):
        return

    if not context.user_data.get("is_authorized", False):
        await query.message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    backend_client = context.bot_data.get("backend_client")
    token = context.user_data.get("backend_token")
    if not isinstance(backend_client, BackendClient) or not isinstance(token, str):
        await query.message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    plan_id = query.data.split(":", maxsplit=1)[1]
    invoice = await backend_client.create_invoice(token, plan_id)
    if invoice.get("ok") is False:
        await query.message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    title = str(invoice.get("title", "Subskrypcja AI Aggregator"))
    description = str(invoice.get("description", f"Plan {plan_id}"))
    stars_amount = int(invoice.get("stars", invoice.get("stars_amount", 0)))

    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=title,
        description=description,
        payload=plan_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars_amount)],
    )


async def handle_precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    if query is None:
        return
    await query.answer(ok=True)


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await access_gate(update, context):
        return

    message = update.effective_message
    user = update.effective_user
    if message is None or user is None or message.successful_payment is None:
        return

    if not context.user_data.get("is_authorized", False):
        await message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    backend_client = context.bot_data.get("backend_client")
    token = context.user_data.get("backend_token")
    if not isinstance(backend_client, BackendClient) or not isinstance(token, str):
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    payment = message.successful_payment
    plan_id = payment.invoice_payload
    stars = payment.total_amount
    charge_id = payment.telegram_payment_charge_id

    result = await backend_client.confirm_payment(token, plan_id, stars, charge_id)
    if result.get("ok") is False:
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    plan_name = str(result.get("plan", result.get("tier", plan_id)))
    expires_at = str(result.get("expires_at", "brak daty"))
    await message.reply_text(f"✅ Plan {plan_name} aktywowany do {expires_at}!")


async def handle_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    subscription = await backend_client.get_subscription(token)
    if subscription.get("ok") is False:
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    tier = str(subscription.get("tier", "free"))
    expires_at = str(subscription.get("expires_at", "brak daty"))
    await message.reply_text(f"Aktualny plan: {tier}\nWażny do: {expires_at}")
