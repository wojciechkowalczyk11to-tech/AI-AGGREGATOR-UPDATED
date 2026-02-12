from __future__ import annotations
import json, os
from pydantic import BaseModel, Field
class ProviderRule(BaseModel):
    enabled: bool = True
    daily_usd_cap: float | None = None
class ProviderPolicy(BaseModel):
    providers: dict[str, ProviderRule] = Field(default_factory=dict)
class ProviderPolicyConfig(BaseModel):
    default: ProviderPolicy = Field(default_factory=ProviderPolicy)
    users: dict[str, ProviderPolicy] = Field(default_factory=dict)
class ProviderPolicyService:
    def __init__(self, config): self.config = config
    @classmethod
    def from_env(cls):
        try: return cls(ProviderPolicyConfig.model_validate(json.loads(os.environ.get("PROVIDER_POLICY_JSON", "{}"))))
        except: return cls(ProviderPolicyConfig())
    def get_effective_policy(self, tid):
        user_policy = self.config.users.get(str(tid))
        if not user_policy: return self.config.default
        merged = self.config.default.providers.copy()
        merged.update(user_policy.providers)
        return ProviderPolicy(providers=merged)
    def is_provider_enabled(self, tid, provider):
        return self.get_effective_policy(tid).providers.get(provider, ProviderRule()).enabled
    def filter_provider_chain(self, tid, chain):
        return [p for p in chain if self.is_provider_enabled(tid, p)]
