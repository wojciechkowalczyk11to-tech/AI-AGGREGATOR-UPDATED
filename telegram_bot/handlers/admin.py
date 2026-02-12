from __future__ import annotations

from middleware.access_control import access_gate, is_admin
from services.backend_client import BackendClient
from telegram import Update
from telegram.ext import ContextTypes


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await access_gate(update, context):
        return

    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    settings = context.bot_data.get("settings")
    if settings is None or not is_admin(user.id, settings):
        await message.reply_text("Brak uprawnień administratora.")
        return

    backend_client = context.bot_data.get("backend_client")
    if not isinstance(backend_client, BackendClient):
        await message.reply_text("Serwer chwilowo niedostępny. Spróbuj za chwilę.")
        return

    token = context.user_data.get("backend_token")
    if not isinstance(token, str) or not token:
        await message.reply_text("Brak sesji administracyjnej. Użyj /start i spróbuj ponownie.")
        return

    if not context.args:
        await message.reply_text(
            "Użycie:\n/admin status\n/admin users\n/admin add <tid> <role>\n/admin role <tid> <role>"
        )
        return

    command = context.args[0].lower()

    if command == "status":
        result = await backend_client.get_admin_overview(token)
        if result.get("ok") is False:
            await message.reply_text(str(result.get("error", "Błąd backendu")))
            return
        await message.reply_text(
            "Panel administracyjny:\n"
            f"Użytkownicy: {result.get('total_users', 0)}\n"
            f"Aktywni dziś: {result.get('active_today', 0)}\n"
            f"Koszt dziś: {result.get('total_cost_today', 0)} USD\n"
            f"Dostawcy: {', '.join(result.get('providers_available', [])) or 'brak'}"
        )
        return

    if command == "users":
        result = await backend_client.get_admin_users(token)
        if result.get("ok") is False:
            await message.reply_text(str(result.get("error", "Błąd backendu")))
            return
        users = result if isinstance(result, list) else result.get("data")
        if not isinstance(users, list):
            await message.reply_text("Brak danych użytkowników.")
            return
        lines = ["Użytkownicy:"]
        for user_item in users[:20]:
            lines.append(f"- {user_item.get('telegram_id')} | {user_item.get('role')}")
        await message.reply_text("\n".join(lines))
        return

    if command == "add":
        if len(context.args) < 3:
            await message.reply_text("Użycie: /admin add <tid> <role>")
            return
        try:
            telegram_id = int(context.args[1])
        except ValueError:
            await message.reply_text("Telegram ID musi być liczbą.")
            return
        role = context.args[2]
        result = await backend_client.admin_add_user(token, telegram_id, role)
        if result.get("ok") is False:
            await message.reply_text(str(result.get("error", "Błąd backendu")))
            return
        await message.reply_text(f"Dodano/zmieniono użytkownika {telegram_id} na rolę {result.get('role')}.")
        return

    if command == "role":
        if len(context.args) < 3:
            await message.reply_text("Użycie: /admin role <tid> <role>")
            return
        try:
            telegram_id = int(context.args[1])
        except ValueError:
            await message.reply_text("Telegram ID musi być liczbą.")
            return
        role = context.args[2]
        result = await backend_client.admin_change_role(token, telegram_id, role)
        if result.get("ok") is False:
            await message.reply_text(str(result.get("error", "Błąd backendu")))
            return
        await message.reply_text(f"Zmieniono rolę użytkownika {telegram_id} na {result.get('role')}.")
        return

    await message.reply_text("Nieznana komenda admina.")
