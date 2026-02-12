from __future__ import annotations
import logging, sys, json
from telegram.ext import ApplicationBuilder
from config import settings
from handlers import register_all_handlers
from services.auth_service import AuthService
from services.chat_service import ChatService
from services.rag_service import RagService
from services.analytics_service import AnalyticsService
from services.image_service import ImageService
from services.agent_service import AgentService
from services.admin_service import AdminService
from services.provider_policy_service import ProviderPolicyService
def main():
    if not settings: sys.exit(1)
    app = ApplicationBuilder().token(settings.telegram_bot_token).build()
    base = settings.backend_url
    app.bot_data.update({
        "auth_service": AuthService(base), "chat_service": ChatService(base),
        "rag_service": RagService(base), "analytics_service": AnalyticsService(base),
        "image_service": ImageService(base), "agent_service": AgentService(base),
        "admin_service": AdminService(base), "policy_service": ProviderPolicyService.from_env(),
        "settings": settings
    })
    register_all_handlers(app)
    app.run_polling()
if __name__ == "__main__": main()
