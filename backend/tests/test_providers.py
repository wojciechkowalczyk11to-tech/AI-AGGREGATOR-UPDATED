from __future__ import annotations

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.exceptions import ProviderError
from app.providers.deepseek import DeepSeekProvider
from app.providers.groq import GroqProvider
from app.providers.grok import GrokProvider
from app.providers.openrouter import OpenRouterProvider


@pytest.mark.asyncio
@respx.mock
async def test_deepseek_generate() -> None:
    route = respx.post("https://api.deepseek.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "DeepSeek OK"}}],
                "usage": {"prompt_tokens": 1000, "completion_tokens": 2000},
            },
        )
    )
    provider = DeepSeekProvider(Settings(DEEPSEEK_API_KEY="test"))

    result = await provider.generate(
        messages=[{"role": "user", "content": "Test"}],
        profile="smart",
        max_tokens=32,
        temperature=0.1,
    )

    assert route.called
    assert result.text == "DeepSeek OK"
    assert result.model == "deepseek-chat"
    assert result.cost_usd > 0


@pytest.mark.asyncio
@respx.mock
async def test_groq_generate() -> None:
    respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Groq works"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            },
        )
    )
    provider = GroqProvider(Settings(GROQ_API_KEY="test"))

    result = await provider.generate(
        messages=[{"role": "user", "content": "Test"}],
        profile="eco",
        max_tokens=32,
        temperature=0.1,
    )

    assert result.provider == "groq"
    assert result.cost_usd == 0.0


@pytest.mark.asyncio
@respx.mock
async def test_openrouter_generate() -> None:
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers["HTTP-Referer"] = request.headers.get("HTTP-Referer", "")
        captured_headers["X-Title"] = request.headers.get("X-Title", "")
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "OpenRouter works"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 7},
            },
        )

    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(side_effect=handler)
    provider = OpenRouterProvider(Settings(OPENROUTER_API_KEY="test"))

    result = await provider.generate(
        messages=[{"role": "user", "content": "Test"}],
        profile="deep",
        max_tokens=32,
        temperature=0.1,
    )

    assert result.provider == "openrouter"
    assert captured_headers["HTTP-Referer"] == "https://jarvis-ai.app"
    assert captured_headers["X-Title"] == "Jarvis AI Aggregator"


@pytest.mark.asyncio
@respx.mock
async def test_grok_generate() -> None:
    respx.post("https://api.x.ai/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Grok response"}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200},
            },
        )
    )
    provider = GrokProvider(Settings(XAI_API_KEY="test"))

    result = await provider.generate(
        messages=[{"role": "user", "content": "Test"}],
        profile="smart",
        max_tokens=32,
        temperature=0.1,
    )

    assert result.model == "grok-2"
    assert result.cost_usd > 0


@pytest.mark.asyncio
@respx.mock
async def test_provider_timeout_raises() -> None:
    def timeout_handler(_: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout")

    respx.post("https://api.deepseek.com/v1/chat/completions").mock(side_effect=timeout_handler)
    provider = DeepSeekProvider(Settings(DEEPSEEK_API_KEY="test"))

    with pytest.raises(ProviderError, match="Przekroczono limit czasu"):
        await provider.generate(
            messages=[{"role": "user", "content": "Test"}],
            profile="eco",
            max_tokens=32,
            temperature=0.1,
        )


@pytest.mark.asyncio
@respx.mock
async def test_openai_compat_retry_on_429() -> None:
    route = respx.post("https://api.deepseek.com/v1/chat/completions")
    route.side_effect = [
        httpx.Response(429, json={"error": {"message": "rate limit"}}),
        httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "OK after retry"}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 22},
            },
        ),
    ]
    provider = DeepSeekProvider(Settings(DEEPSEEK_API_KEY="test"))

    result = await provider.generate(
        messages=[{"role": "user", "content": "Test"}],
        profile="eco",
        max_tokens=32,
        temperature=0.1,
    )

    assert route.call_count == 2
    assert result.text == "OK after retry"
