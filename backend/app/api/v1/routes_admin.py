from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.db.models import User, UserRole
from app.services.admin_service import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


def _parse_admin_user_ids(raw_value: str) -> set[int]:
    admin_ids: set[int] = set()
    for item in raw_value.split(","):
        stripped = item.strip()
        if not stripped:
            continue
        try:
            admin_ids.add(int(stripped))
        except ValueError:
            continue
    return admin_ids


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    settings = get_settings()
    admin_ids = _parse_admin_user_ids(settings.ADMIN_USER_IDS)
    if current_user.role != UserRole.FULL_ACCESS or current_user.telegram_id not in admin_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Brak uprawnień administratora.",
        )
    return current_user


class AdminAddUserRequest(BaseModel):
    telegram_id: int
    role: str


class AdminChangeRoleRequest(BaseModel):
    role: str


@router.get("/overview")
async def get_overview(
    _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    return await admin_service.get_overview(db)


@router.get("/users")
async def get_users(
    limit: int = 50,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    return await admin_service.list_users(db, limit=limit)


@router.post("/users")
async def create_user(
    payload: AdminAddUserRequest,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await admin_service.add_user(payload.telegram_id, payload.role, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/users/{telegram_id}/role")
async def update_user_role(
    telegram_id: int,
    payload: AdminChangeRoleRequest,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await admin_service.change_role(telegram_id, payload.role, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/users/{telegram_id}")
async def delete_user(
    telegram_id: int,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    deleted = await admin_service.remove_user(telegram_id, db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Użytkownik nie istnieje."
        )
    return {"success": True}
