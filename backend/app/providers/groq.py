from __future__ import annotations

from app.core.config import Settings
from app.providers.openai_compat import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    fallback_models: list[str] = ["mixtral-8x7b-32768", "gemma2-9b-it"]

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            name="groq",
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            models={
                "eco": "llama-3.3-70b-versatile",
                "smart": "llama-3.3-70b-versatile",
                "deep": "llama-3.3-70b-versatile",
            },
            costs={
                "llama-3.3-70b-versatile": (0.0, 0.0),
                "mixtral-8x7b-32768": (0.0, 0.0),
                "gemma2-9b-it": (0.0, 0.0),
            },
            default_headers=None,
        )
