from __future__ import annotations

from middleware.auth import with_auth_retry
from middleware.typing_indicator import TypingIndicator
from services.provider_normalization import canonical_provider
from utils.formatters import safe_markdown_v2
from utils.message_splitter import split_message
from utils.meta_footer import format_meta_footer


async def handle_model_command(update, context):
    cmd = update.message.text.split()[0][1:]
    prov = canonical_provider(cmd)
    if not context.args:
        auth_svc = context.bot_data["auth_service"]
        await with_auth_retry(
            lambda uid, tok: auth_svc.update_settings(uid, tok, {"preferred_model": prov}),
            update,
            context,
            auth_svc,
        )
        await update.message.reply_text(f"✅ Zmieniono na {prov}")
        return
    chat_svc, auth_svc = context.bot_data["chat_service"], context.bot_data["auth_service"]
    async with TypingIndicator(update, context):
        res = await with_auth_retry(
            lambda uid, tok: chat_svc.send_with_provider(
                uid,
                tok,
                " ".join(context.args),
                prov,
                conversation_id=context.user_data.get("conv_id"),
            ),
            update,
            context,
            auth_svc,
        )
        context.user_data["conv_id"] = res.get("conversation_id")
        total_tokens = res.get("input_tokens", 0) + res.get("output_tokens", 0)
        footer = format_meta_footer(
            res.get("model_name", prov),
            res.get("cost_usd", 0),
            total_tokens,
            res.get("_elapsed", 0),
        )
        full = res.get("response", "") + footer
        for chunk in split_message(full):
            try:
                await update.message.reply_text(safe_markdown_v2(chunk), parse_mode="MarkdownV2")
            except Exception:
                await update.message.reply_text(chunk)
