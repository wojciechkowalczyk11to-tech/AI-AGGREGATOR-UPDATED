from __future__ import annotations
import base64, io
from middleware.auth import with_auth_retry
async def handle(update, context):
    if not context.args: return await update.message.reply_text("Opisz obraz.")
    img_svc, auth_svc = context.bot_data["image_service"], context.bot_data["auth_service"]
    res = await with_auth_retry(lambda uid, tok: img_svc.generate_image(tok, " ".join(context.args)), update, context, auth_svc)
    if res.get("image_base64"):
        await update.message.reply_photo(io.BytesIO(base64.b64decode(res["image_base64"])))
    elif res.get("image_url"):
        await update.message.reply_photo(res["image_url"])
