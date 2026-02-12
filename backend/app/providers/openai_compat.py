from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from app.core.exceptions import ProviderError
from app.providers.base import AbstractProvider, ProviderResult


class OpenAICompatibleProvider(AbstractProvider):
    def __init__(
        self,
        name: str,
        api_key: str,
        base_url: str,
        models: dict[str, str],
        costs: dict[str, tuple[float, float]],
        default_headers: dict[str, str] | None = None,
    ) -> None:
        self._name = name
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._models = models
        self._costs = costs
        self._default_headers = default_headers or {}

    @property
    def name(self) -> str:
        return self._name

    async def generate(
        self,
        messages: list[dict[str, str]],
        profile: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResult:
        model_candidates = self._get_model_candidates(profile)
        last_error: ProviderError | None = None
        for model_name in model_candidates:
            try:
                return await self._generate_with_model(
                    messages=messages,
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except ProviderError as exc:
                last_error = exc
                continue

        raise last_error or ProviderError("Nie udało się uzyskać odpowiedzi od providera")

    async def _generate_with_model(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> ProviderResult:
        endpoint = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            **self._default_headers,
        }
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        start = time.perf_counter()
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(endpoint, json=payload, headers=headers)
                if response.status_code in {429, 500, 502, 503} and attempt == 0:
                    await asyncio.sleep(0.2)
                    continue
                response.raise_for_status()
                data = response.json()
                return self._parse_result(data=data, model=model, start=start)
            except httpx.TimeoutException as exc:
                raise ProviderError("Przekroczono limit czasu odpowiedzi providera") from exc
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                last_exc = exc
                if isinstance(exc, httpx.HTTPStatusError):
                    code = exc.response.status_code
                    if code in {429, 500, 502, 503} and attempt == 0:
                        await asyncio.sleep(0.2)
                        continue
                break

        raise ProviderError(f"Błąd wywołania providera {self.name}") from last_exc

    def _parse_result(self, data: dict[str, Any], model: str, start: float) -> ProviderResult:
        try:
            text = str(data["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider zwrócił nieprawidłowy format odpowiedzi") from exc

        usage = data.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        in_rate, out_rate = self._costs.get(model, (0.0, 0.0))
        cost_usd = (input_tokens * in_rate / 1_000_000) + (output_tokens * out_rate / 1_000_000)
        latency_ms = int((time.perf_counter() - start) * 1000)

        return ProviderResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            fallback_used=False,
        )

    def _get_model_candidates(self, profile: str) -> list[str]:
        selected = self._models.get(profile, self._models.get("eco", ""))
        if not selected:
            raise ProviderError("Brak skonfigurowanego modelu dla wybranego profilu")
        fallback_models: list[str] = list(getattr(self, "fallback_models", []))
        return [selected, *[model for model in fallback_models if model != selected]]

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
