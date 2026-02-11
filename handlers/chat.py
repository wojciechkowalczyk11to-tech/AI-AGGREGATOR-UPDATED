from __future__ import annotations
import logging
from middleware.auth import with_auth_retry
from middleware.typing_indicator import TypingIndicator
from utils.meta_footer import format_meta_footer
from utils.message_splitter import split_message, should_send_as_file
from utils.formatters import safe_markdown_v2
async def handle(update, context):
    if not update.message or not update.message.text: return
    chat_svc, auth_svc = context.bot_data["chat_service"], context.bot_data["auth_service"]
    async with TypingIndicator(update, context):
        try:
            res = await with_auth_retry(lambda uid, tok: chat_svc.send_message(uid, tok, update.message.text, conversation_id=context.user_data.get("conv_id")), update, context, auth_svc)
            context.user_data["conv_id"] = res.get("conversation_id")
            footer = format_meta_footer(res.get("model_name", "AI"), res.get("cost_usd", 0), (res.get("input_tokens", 0)+res.get("output_tokens", 0)), res.get("_elapsed", 0), res.get("fallback", False))
            full = res.get("response", "") + footer
            if should_send_as_file(full):
                from io import BytesIO
                bio = BytesIO(full.encode()); bio.name = "response.md"
                await update.message.reply_document(bio, caption="📄 Długa odpowiedź.")
                return
            for chunk in split_message(full):
                try: await update.message.reply_text(safe_markdown_v2(chunk), parse_mode="MarkdownV2")
                except: await update.message.reply_text(chunk)
        except Exception as e:
            await update.message.reply_text(f"❌ Błąd: {e}")
