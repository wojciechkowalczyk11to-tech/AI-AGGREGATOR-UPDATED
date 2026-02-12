from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.v1.routes_admin import require_admin
from app.db.models import User
from app.services.invite_service import invite_service

router = APIRouter(prefix="/invite", tags=["invite"])


class ValidateInviteRequest(BaseModel):
    code: str


class ConsumeInviteRequest(BaseModel):
    code: str
    telegram_id: int


class CreateInviteRequest(BaseModel):
    role: str
    ttl_hours: int
    max_uses: int


@router.post("/validate")
async def validate_invite(payload: ValidateInviteRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    role = await invite_service.validate_invite(payload.code, db)
    return {"valid": role is not None, "role": role}


@router.post("/consume")
async def consume_invite(payload: ConsumeInviteRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await invite_service.consume_invite(payload.code, payload.telegram_id, db)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nieprawidłowy lub wygasły kod.",
        )
    return result


@router.post("/create")
async def create_invite(
    payload: CreateInviteRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        code = await invite_service.create_invite(
            admin_tid=current_user.telegram_id,
            role=payload.role,
            ttl_hours=payload.ttl_hours,
            max_uses=payload.max_uses,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"code": code}
