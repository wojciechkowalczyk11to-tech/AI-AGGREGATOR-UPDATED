from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import logging

class BotSettings(BaseSettings):
    telegram_bot_token: str = Field(..., description="Telegram Bot Token")
    telegram_mode: str = Field("polling", description="'polling' or 'webhook'")
    webhook_url: str = Field("", description="Base URL for webhooks")
    webhook_port: int = Field(8443, description="Port for webhooks")
    webhook_path: str = Field("webhook", description="URL path for webhooks")
    webhook_secret_token: str = Field("", description="Secret token for webhook")
    backend_url: str = Field("http://localhost:8000", description="URL of the backend")
    allowed_user_ids: list[int] = Field(default_factory=list, description="Allowed IDs")
    admin_user_ids: list[int] = Field(default_factory=list, description="Admin IDs")
    voice_enabled: bool = True
    inline_enabled: bool = True
    image_gen_enabled: bool = True
    notebook_mode_enabled: bool = True
    provider_policy_json: str = Field('{"default":{"providers":{"gemini":{"enabled":true},"deepseek":{"enabled":true},"groq":{"enabled":true,"daily_usd_cap":1.0}}}}')
    log_level: str = "INFO"
    log_json: bool = True
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    @property
    def is_webhook_mode(self) -> bool:
        return self.telegram_mode.lower() == "webhook"

try:
    settings = BotSettings()
except Exception:
    settings = None
