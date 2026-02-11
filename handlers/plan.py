from __future__ import annotations
from keyboards.plan_keyboard import get_plan_keyboard
async def handle(update, context):
    await update.message.reply_text(f"💎 Plan: {context.user_data.get('tier', 'basic')}", reply_markup=get_plan_keyboard())
