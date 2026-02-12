from __future__ import annotations
async def handle(update, context):
    help_text = "🔍 *Dostępne komendy:*\n/start, /help, /settings, /usage, /plan, /new, /forget, /imagine, /rag, /upload, /workspace, /repurpose\n\n🤖 *Modele:* /gemini, /claude, /gpt, /deepseek, /groq, /mistral, /grok, /openrouter"
    await update.message.reply_markdown_v2(help_text.replace(".", "\\.").replace("-", "\\-").replace("!", "\\!"))
