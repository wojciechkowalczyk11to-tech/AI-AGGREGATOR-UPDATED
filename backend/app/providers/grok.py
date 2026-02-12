from __future__ import annotations

from app.core.config import Settings
from app.providers.openai_compat import OpenAICompatibleProvider


class GrokProvider(OpenAICompatibleProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            name="grok",
            api_key=settings.XAI_API_KEY,
            base_url="https://api.x.ai/v1",
            models={
                "eco": "grok-2",
                "smart": "grok-2",
                "deep": "grok-2",
            },
            costs={"grok-2": (5.0, 15.0)},
            default_headers=None,
        )
