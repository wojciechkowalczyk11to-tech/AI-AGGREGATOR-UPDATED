from __future__ import annotations

import time

import httpx

from app.core.config import Settings
from app.core.exceptions import ProviderError
from app.providers.base import AbstractProvider, ProviderResult


class GeminiProvider(AbstractProvider):
    PROFILE_MODEL_MAP: dict[str, str] = {
        "eco": "gemini-2.0-flash-lite",
        "smart": "gemini-2.0-flash",
        "deep": "gemini-2.0-pro",
    }

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def name(self) -> str:
        return "gemini"

    async def generate(
        self,
        messages: list[dict[str, str]],
        profile: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResult:
        model = self.PROFILE_MODEL_MAP.get(profile, self.PROFILE_MODEL_MAP["eco"])
        contents = [
            {
                "role": "model" if message.get("role") == "assistant" else "user",
                "parts": [{"text": message.get("content", "")}],
            }
            for message in messages
        ]

        start = time.perf_counter()
        endpoint = f"{self._base_url}/{model}:generateContent"
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    params={"key": self._settings.GEMINI_API_KEY},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError("Błąd wywołania providera Gemini") from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        usage = data.get("usageMetadata", {})
        input_tokens = int(usage.get("promptTokenCount", 0))
        output_tokens = int(usage.get("candidatesTokenCount", 0))
        cost = self._calculate_cost(model=model, input_tokens=input_tokens, output_tokens=output_tokens)

        return ProviderResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            fallback_used=False,
        )

    async def health_check(self) -> bool:
        try:
            result = await self.generate(
                messages=[{"role": "user", "content": "ping"}],
                profile="eco",
                max_tokens=5,
                temperature=0.0,
            )
            return bool(result.text)
        except ProviderError:
            return False

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = {
            "gemini-2.0-flash-lite": (0.075 / 1_000_000, 0.30 / 1_000_000),
            "gemini-2.0-flash": (0.10 / 1_000_000, 0.40 / 1_000_000),
            "gemini-2.0-pro": (1.25 / 1_000_000, 5.00 / 1_000_000),
        }
        in_rate, out_rate = rates.get(model, rates["gemini-2.0-flash-lite"])
        return (input_tokens * in_rate) + (output_tokens * out_rate)
