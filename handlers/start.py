from __future__ import annotations
from keyboards.main_menu import get_main_menu_keyboard
async def handle(update, context):
    await update.message.reply_text(f"👋 Witaj {update.effective_user.first_name}! Wybierz model i zacznij rozmowę.", reply_markup=get_main_menu_keyboard())
