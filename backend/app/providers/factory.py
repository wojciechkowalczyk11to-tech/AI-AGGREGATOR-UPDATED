from __future__ import annotations

from app.core.config import Settings
from app.providers.base import AbstractProvider
from app.providers.gemini import GeminiProvider


class ProviderFactory:
    def __init__(self, settings: Settings) -> None:
        self._registry: dict[str, AbstractProvider] = {}
        if settings.GEMINI_API_KEY.strip():
            self.register("gemini", GeminiProvider(settings=settings))

    def register(self, name: str, provider: AbstractProvider) -> None:
        self._registry[name.lower()] = provider

    def get(self, name: str) -> AbstractProvider | None:
        return self._registry.get(name.lower())

    def list_available(self) -> list[str]:
        return sorted(self._registry.keys())
