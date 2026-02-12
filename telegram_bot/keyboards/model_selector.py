from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_model_selector_keyboard(current_model=None, providers=None):
    if not providers:
        providers = ["gemini", "claude", "openai", "deepseek", "groq", "mistral", "grok", "openrouter"]
    keyboard = []
    for i in range(0, len(providers), 2):
        row = []
        for p in providers[i : i + 2]:
            text = f"✅ {p.capitalize()}" if p == current_model else p.capitalize()
            row.append(InlineKeyboardButton(text, callback_data=f"set_model:{p}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)
