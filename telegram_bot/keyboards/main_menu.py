from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🤖 Modele"), KeyboardButton("📊 Statystyki")],
            [KeyboardButton("⚙️ Ustawienia"), KeyboardButton("💎 Plan")],
            [KeyboardButton("📂 Dokumenty"), KeyboardButton("🆘 Pomoc")],
        ],
        resize_keyboard=True,
    )
