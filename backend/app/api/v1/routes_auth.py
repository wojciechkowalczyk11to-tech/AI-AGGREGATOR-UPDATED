from __future__ import annotations

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis
from app.api.v1.schemas import (
    AuthResponse,
    BootstrapRequest,
    BootstrapResponse,
    MeResponse,
    RegisterRequest,
    SettingsUpdateRequest,
    SettingsUpdateResponse,
    UnlockRequest,
    UnlockResponse,
)
from app.db.models import User
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    data = await auth_service.register(payload.telegram_chat_id, db)
    return AuthResponse(**data)


@router.post("/unlock", response_model=UnlockResponse)
async def unlock(
    payload: UnlockRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
) -> UnlockResponse:
    data = await auth_service.unlock(payload.telegram_chat_id, payload.code, db, redis)
    return UnlockResponse(**data)


@router.post("/bootstrap", response_model=BootstrapResponse)
async def bootstrap(
    payload: BootstrapRequest, db: AsyncSession = Depends(get_db)
) -> BootstrapResponse:
    data = await auth_service.bootstrap(payload.telegram_chat_id, payload.bootstrap_code, db)
    return BootstrapResponse(**data)


@router.get("/me", response_model=MeResponse)
async def me(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> MeResponse:
    data = await auth_service.get_me(current_user.id, db)
    return MeResponse(**data)


@router.put("/settings", response_model=SettingsUpdateResponse)
async def update_settings(
    payload: SettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SettingsUpdateResponse:
    data = await auth_service.update_settings(current_user.id, payload.settings, db)
    return SettingsUpdateResponse(**data)
