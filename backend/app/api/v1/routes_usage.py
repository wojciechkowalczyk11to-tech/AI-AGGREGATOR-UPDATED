from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.schemas import UsageLimitsResponse, UsageSummaryResponse
from app.core.config import get_settings
from app.db.models import User
from app.services.policy_engine import policy_engine
from app.services.usage_service import usage_service

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/summary", response_model=UsageSummaryResponse)
async def usage_summary(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageSummaryResponse:
    data = await usage_service.get_usage_summary(current_user.id, days, db)
    return UsageSummaryResponse(**data)


@router.get("/limits", response_model=UsageLimitsResponse)
async def usage_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageLimitsResponse:
    data = await policy_engine.get_remaining_limits(current_user, db, get_settings())
    return UsageLimitsResponse(**data)
