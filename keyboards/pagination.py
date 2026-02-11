from __future__ import annotations
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
def get_pagination_keyboard(cp, tp, pref):
    row = []
    if cp > 1: row.append(InlineKeyboardButton("⬅️", callback_data=f"{pref}:{cp-1}"))
    if cp < tp: row.append(InlineKeyboardButton("➡️", callback_data=f"{pref}:{cp+1}"))
    return InlineKeyboardMarkup([row]) if row else InlineKeyboardMarkup([])
