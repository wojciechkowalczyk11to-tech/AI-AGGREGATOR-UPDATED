from __future__ import annotations

from app.core.config import Settings
from app.providers.openai_compat import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            name="openrouter",
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            models={
                "eco": "google/gemma-2-9b-it:free",
                "smart": "meta-llama/llama-3.3-70b-instruct:free",
                "deep": "qwen/qwen-2.5-72b-instruct:free",
            },
            costs={
                "google/gemma-2-9b-it:free": (0.0, 0.0),
                "meta-llama/llama-3.3-70b-instruct:free": (0.0, 0.0),
                "qwen/qwen-2.5-72b-instruct:free": (0.0, 0.0),
            },
            default_headers={
                "HTTP-Referer": "https://jarvis-ai.app",
                "X-Title": "Jarvis AI Aggregator",
            },
        )
