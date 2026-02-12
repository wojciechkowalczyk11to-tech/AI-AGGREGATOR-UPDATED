from __future__ import annotations

from services.provider_policy_service import ProviderPolicyConfig, ProviderPolicyService


def test_policy():
    c = ProviderPolicyConfig.model_validate({"default": {"providers": {"g": {"enabled": True}}}})
    s = ProviderPolicyService(c)
    assert s.is_provider_enabled(1, "g") is True
