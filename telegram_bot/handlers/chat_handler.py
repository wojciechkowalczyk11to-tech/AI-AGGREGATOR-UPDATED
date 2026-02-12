from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from middleware.access_control import access_gate
from services.backend_client import BackendClient

MAX_MESSAGE_LEN = 4096


def _split_message(text: str, chunk_size: int = MAX_MESSAGE_LEN) -> list[str]:
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)] or [""]


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await access_gate(update, context):
        return

    message = update.effective_message
    if message is None or message.text is None:
        return

    if not context.user_data.get("is_authorized", False):
        await message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    backend_client = context.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    token = context.user_data.get("backend_token")
    if not isinstance(token, str) or not token:
        await message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    mode = str(context.user_data.get("mode", "smart"))
    session_id = context.user_data.get("session_id")
    session_value = session_id if isinstance(session_id, str) else None

    result = await backend_client.chat(token, message.text, session_value, None, mode)
    if result.get("ok") is False:
        error_message = str(
            result.get("error", "Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        )
        if "niedostępny" in error_message.lower():
            await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
            return
        await message.reply_text("Brak dostępu. Użyj /unlock <kod>")
        return

    if isinstance(result.get("session_id"), str):
        context.user_data["session_id"] = result["session_id"]

    answer = str(result.get("response", ""))
    model = str(result.get("model", result.get("model_name", "model")))
    cost = float(result.get("cost", result.get("cost_usd", 0.0)))
    tokens = int(result.get("tokens", result.get("total_tokens", 0)))
    latency = int(result.get("latency", result.get("latency_ms", 0)))
    footer = f"\n\n🤖 {model} | 💳 ${cost:.4f} | ⚡ {tokens} tok | ⏱ {latency}ms"
    full_message = f"{answer}{footer}"

    for chunk in _split_message(full_message):
        await message.reply_text(chunk)
