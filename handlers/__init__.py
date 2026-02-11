from __future__ import annotations
from telegram.ext import CommandHandler, MessageHandler, InlineQueryHandler, CallbackQueryHandler, filters
def register_all_handlers(app):
    from handlers import start, help, commands, chat, settings_cmd, usage, plan, voice, documents, images, rag, admin, inline, callbacks, notebook, workspace, memory, repurpose, errors
    app.add_handler(CommandHandler("start", start.handle))
    app.add_handler(CommandHandler("help", help.handle))
    app.add_handler(CommandHandler("settings", settings_cmd.handle))
    app.add_handler(CommandHandler("usage", usage.handle))
    app.add_handler(CommandHandler("plan", plan.handle))
    app.add_handler(CommandHandler("memory", memory.handle_memory))
    app.add_handler(CommandHandler("forget", memory.handle_forget))
    app.add_handler(CommandHandler("new", memory.handle_new_conversation))
    app.add_handler(CommandHandler("export", memory.handle_export))
    app.add_handler(CommandHandler("imagine", images.handle))
    app.add_handler(CommandHandler("rag", rag.handle_search))
    app.add_handler(CommandHandler("upload", rag.handle_upload_command))
    app.add_handler(CommandHandler("notebook", notebook.handle))
    app.add_handler(CommandHandler("workspace", workspace.handle_list))
    app.add_handler(CommandHandler("download", workspace.handle_download))
    app.add_handler(CommandHandler("repurpose", repurpose.handle))
    app.add_handler(CommandHandler("admin", admin.handle))
    for cmd in ["claude", "gpt", "gemini", "deepseek", "groq", "mistral", "grok", "openrouter"]:
        app.add_handler(CommandHandler(cmd, commands.handle_model_command))
    app.add_handler(InlineQueryHandler(inline.handle))
    app.add_handler(CallbackQueryHandler(callbacks.handle))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice.handle))
    app.add_handler(MessageHandler(filters.Document.ALL, documents.handle))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat.handle))
    app.add_error_handler(errors.handle_error)
