from __future__ import annotations

from keyboards.plan_keyboard import get_plan_keyboard


async def handle(update, context):
    tier = context.user_data.get("tier", "basic")
    await update.message.reply_text(f"💎 Plan: {tier}", reply_markup=get_plan_keyboard())
