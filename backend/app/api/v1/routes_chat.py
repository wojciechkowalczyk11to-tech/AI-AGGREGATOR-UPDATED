from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.schemas import ChatRequest, ChatResponse, ProvidersResponse
from app.core.config import get_settings
from app.db.models import User
from app.providers.factory import ProviderFactory
from app.services.orchestrator import build_orchestrator

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    orchestrator = build_orchestrator()
    sid = uuid.UUID(payload.session_id) if payload.session_id else None
    data = await orchestrator.process_chat(
        user=current_user,
        prompt=payload.prompt,
        session_id=sid,
        provider_pref=payload.provider,
        mode=payload.mode,
        db=db,
    )
    return ChatResponse(**data)


@router.get("/providers", response_model=ProvidersResponse)
async def providers() -> ProvidersResponse:
    factory = ProviderFactory(get_settings())
    return ProvidersResponse(providers=factory.list_available())
