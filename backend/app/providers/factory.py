from __future__ import annotations

from app.core.config import Settings
from app.providers.base import AbstractProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.grok import GrokProvider
from app.providers.openrouter import OpenRouterProvider


class ProviderFactory:
    def __init__(self, settings: Settings) -> None:
        self._registry: dict[str, AbstractProvider] = {}
        if settings.GEMINI_API_KEY.strip():
            self.register("gemini", GeminiProvider(settings=settings))
        if settings.DEEPSEEK_API_KEY.strip():
            self.register("deepseek", DeepSeekProvider(settings=settings))
        if settings.GROQ_API_KEY.strip():
            self.register("groq", GroqProvider(settings=settings))
        if settings.OPENROUTER_API_KEY.strip():
            self.register("openrouter", OpenRouterProvider(settings=settings))
        if settings.XAI_API_KEY.strip():
            self.register("grok", GrokProvider(settings=settings))

    def register(self, name: str, provider: AbstractProvider) -> None:
        self._registry[name.lower()] = provider

    def get(self, name: str) -> AbstractProvider | None:
        return self._registry.get(name.lower())

    def list_available(self) -> list[str]:
        return sorted(self._registry.keys())
