from __future__ import annotations

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)


def register_all_handlers(app: Application) -> None:
    from handlers import (
        admin,
        chat_handler,
        help,
        invite,
        mode,
        payments,
        start,
        unlock,
        usage,
        whoami,
    )

    app.add_handler(PreCheckoutQueryHandler(payments.handle_precheckout))

    app.add_handler(CommandHandler("start", start.handle))
    app.add_handler(CommandHandler("help", help.handle))
    app.add_handler(CommandHandler("unlock", unlock.handle))
    app.add_handler(CommandHandler("whoami", whoami.handle))
    app.add_handler(CommandHandler("mode", mode.handle))
    app.add_handler(CommandHandler("usage", usage.handle))
    app.add_handler(CommandHandler("subscribe", payments.handle_subscribe))
    app.add_handler(CommandHandler("plan", payments.handle_plan))
    app.add_handler(CommandHandler("admin", admin.handle))
    app.add_handler(CommandHandler("invite", invite.handle))

    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payments.handle_successful_payment))
    app.add_handler(CallbackQueryHandler(payments.handle_buy_callback, pattern=r"^buy:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler.handle))
