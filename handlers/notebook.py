from __future__ import annotations
async def handle(update, context):
    context.user_data["nb"] = not context.user_data.get("nb", False)
    await update.message.reply_text(f"📝 Notebook: {'WŁ' if context.user_data['nb'] else 'WYŁ'}")
