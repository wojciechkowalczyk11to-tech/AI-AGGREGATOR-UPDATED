from __future__ import annotations

from services.provider_normalization import canonical_provider


def test_norm():
    assert canonical_provider("gpt") == "openai"
