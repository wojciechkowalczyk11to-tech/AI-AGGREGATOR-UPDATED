from __future__ import annotations

from app.core.config import Settings
from app.providers.openai_compat import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            name="deepseek",
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
            models={
                "eco": "deepseek-chat",
                "smart": "deepseek-chat",
                "deep": "deepseek-reasoner",
            },
            costs={
                "deepseek-chat": (0.14, 0.28),
                "deepseek-reasoner": (0.55, 2.19),
            },
            default_headers=None,
        )
