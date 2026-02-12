from __future__ import annotations

import asyncio
import uuid

from middleware.auth import with_auth_retry
from telegram import InlineQueryResultArticle, InputTextMessageContent
from utils.meta_footer import format_meta_footer


async def handle(update, context):
    q = update.inline_query.query
    if not q:
        return
    chat_svc, auth_svc = context.bot_data["chat_service"], context.bot_data["auth_service"]

    async def get_res(p):
        try:
            r = await with_auth_retry(
                lambda uid, tok: chat_svc.send_with_provider(uid, tok, q, p),
                update,
                context,
                auth_svc,
            )
            total_tokens = r.get("input_tokens", 0) + r.get("output_tokens", 0)
            footer = format_meta_footer(
                r.get("model_name", p),
                r.get("cost_usd", 0),
                total_tokens,
                r.get("_elapsed", 0),
            )
            return p, r.get("response", "") + footer
        except Exception:
            return p, "Error"

    results = []
    responses = await asyncio.gather(*[get_res(p) for p in ["gemini", "groq"]])
    for p, res in responses:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=p.capitalize(),
                input_message_content=InputTextMessageContent(res, parse_mode="Markdown"),
            )
        )
    await update.inline_query.answer(results, cache_time=60)
