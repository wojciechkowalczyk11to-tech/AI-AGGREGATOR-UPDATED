from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_settings_keyboard(settings):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🤖 Wybierz model", callback_data="menu:models")],
            [
                InlineKeyboardButton("📝 Tryb Notebook", callback_data="toggle:notebook"),
                InlineKeyboardButton("🧠 Pamięć", callback_data="menu:memory"),
            ],
            [InlineKeyboardButton("🧹 Wyczyść historię", callback_data="confirm:forget")],
        ]
    )
