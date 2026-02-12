from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    DATABASE_URL: str = ''
    REDIS_URL: str = 'redis://localhost:6379/0'

    JWT_SECRET_KEY: str = ''
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRE_HOURS: int = 24

    GEMINI_API_KEY: str = ''
    DEEPSEEK_API_KEY: str = ''
    GROQ_API_KEY: str = ''
    OPENROUTER_API_KEY: str = ''
    XAI_API_KEY: str = ''
    OPENAI_API_KEY: str = ''
    ANTHROPIC_API_KEY: str = ''

    VERTEX_PROJECT_ID: str = ''
    VERTEX_LOCATION: str = ''
    VERTEX_SEARCH_DATASTORE_ID: str = ''

    DEMO_UNLOCK_CODE: str = ''
    BOOTSTRAP_ADMIN_CODE: str = ''
    FULL_TELEGRAM_IDS: str = ''
    DEMO_TELEGRAM_IDS: str = ''

    LOG_LEVEL: str = 'INFO'
    LOG_JSON: bool = True

    DEMO_GROK_DAILY: int = 5
    DEMO_WEB_DAILY: int = 5
    DEMO_SMART_CREDITS_DAILY: int = 20
    FULL_DAILY_USD_CAP: float = 5.0
    RATE_LIMIT_PER_MINUTE: int = 30

    VOICE_ENABLED: bool = True
    GITHUB_ENABLED: bool = True
    VERTEX_ENABLED: bool = False
    PAYMENTS_ENABLED: bool = False
    WEB_SEARCH_ENABLED: bool = True
    RAG_ENABLED: bool = True
    IMAGE_ENABLED: bool = True
    DOCUMENTS_ENABLED: bool = True
    NOTEBOOK_ENABLED: bool = True
    ADMIN_ENABLED: bool = True

    POSTGRES_PASSWORD: str = ''
    DB_PASSWORD: str = ''
    TELEGRAM_BOT_TOKEN: str = ''
    BACKEND_URL: str = 'http://localhost:8000'
    ALLOWED_USER_IDS: str = ''
    ADMIN_USER_IDS: str = ''


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
