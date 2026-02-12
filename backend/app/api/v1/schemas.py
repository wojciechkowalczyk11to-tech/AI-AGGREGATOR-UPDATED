from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    telegram_chat_id: int


class UnlockRequest(BaseModel):
    telegram_chat_id: int
    code: str


class BootstrapRequest(BaseModel):
    telegram_chat_id: int
    bootstrap_code: str


class AuthResponse(BaseModel):
    id: str
    telegram_id: int
    role: str
    authorized: bool
    access_token: str


class UnlockResponse(BaseModel):
    success: bool
    role: str


class BootstrapResponse(BaseModel):
    success: bool


class MeResponse(BaseModel):
    id: str
    telegram_id: int
    role: str
    authorized: bool
    verified: bool
    default_mode: str
    settings: dict[str, Any]


class SettingsUpdateRequest(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class SettingsUpdateResponse(BaseModel):
    settings: dict[str, Any]


class ChatRequest(BaseModel):
    prompt: str
    session_id: str | None = None
    provider: str | None = None
    mode: str = "eco"


class ChatMeta(BaseModel):
    model: str
    provider: str
    cost_usd: float
    input_tokens: int
    output_tokens: int
    latency_ms: int
    fallback_used: bool


class ChatResponse(BaseModel):
    response: str
    meta: ChatMeta
    session_id: str


class ProvidersResponse(BaseModel):
    providers: list[str]


class UsageSummaryResponse(BaseModel):
    days: int
    total_requests: int
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    by_provider: dict[str, dict[str, float | int]]


class UsageLimitsResponse(BaseModel):
    grok_remaining: int
    smart_credits_remaining: int
    daily_budget_remaining: float
