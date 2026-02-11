from __future__ import annotations
_ALIASES = {
    "gpt": "openai", "gpt-4": "openai", "gpt-4o": "openai", "openai": "openai",
    "claude": "claude", "anthropic": "claude", "gemini": "gemini", "google": "gemini",
    "deepseek": "deepseek", "groq": "groq", "grok": "grok", "xai": "grok",
    "mistral": "mistral", "openrouter": "openrouter",
}
def canonical_provider(name: str | None) -> str:
    if not name: return ""
    raw = name.strip().lower()
    return _ALIASES.get(raw, raw)
