from __future__ import annotations
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
def get_plan_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🌟 Kup Premium", url="https://t.me/your_payment_bot")], [InlineKeyboardButton("📊 Porównaj plany", callback_data="plan:compare")]])
