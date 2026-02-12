from __future__ import annotations

import sys

from config import settings
from handlers import register_all_handlers
from services.backend_client import BackendClient
from telegram.ext import Application, ApplicationBuilder


async def _post_init(app: Application) -> None:
    app.bot_data["backend_client"] = BackendClient(app.bot_data["settings"].backend_url)


async def _post_shutdown(app: Application) -> None:
    backend_client = app.bot_data.get("backend_client")
    if isinstance(backend_client, BackendClient):
        await backend_client.close()


def main() -> None:
    if not settings:
        sys.exit(1)

    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )
    app.bot_data["settings"] = settings

    register_all_handlers(app)
    app.run_polling()


if __name__ == "__main__":
    main()
