from __future__ import annotations
import tempfile, os
from utils.voice_processor import convert_ogg_to_wav, cleanup_files
from handlers import chat
from middleware.auth import with_auth_retry
async def handle(update, context):
    voice = update.message.voice
    chat_svc, auth_svc = context.bot_data["chat_service"], context.bot_data["auth_service"]
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_tmp: ogg_path = ogg_tmp.name
    wav_path = ogg_path.replace(".ogg", ".wav")
    try:
        f = await context.bot.get_file(voice.file_id)
        await f.download_to_drive(ogg_path)
        if not convert_ogg_to_wav(ogg_path, wav_path):
            await update.message.reply_text("❌ Błąd konwersji audio.")
            return
        res = await with_auth_retry(lambda uid, tok: chat_svc.transcribe(tok, wav_path), update, context, auth_svc)
        update.message.text = res.get("text", "")
        await chat.handle(update, context)
    finally: cleanup_files(ogg_path, wav_path)
