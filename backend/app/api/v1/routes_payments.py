from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.schemas import (
    PaymentConfirmRequest,
    PaymentInvoiceRequest,
    PaymentResponse,
    PaymentSubscriptionResponse,
    PaymentRefundRequest,
    PlanListResponse,
)
from app.db.models import Payment, User, UserRole
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/plans", response_model=PlanListResponse)
async def get_plans() -> PlanListResponse:
    plans = await payment_service.get_plans()
    return PlanListResponse(plans=plans)


@router.post("/invoice", response_model=dict[str, object])
async def create_invoice(
    payload: PaymentInvoiceRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    _ = current_user
    try:
        return await payment_service.create_invoice(payload.plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payload: PaymentConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    try:
        payment = await payment_service.process_payment(
            user_id=current_user.id,
            plan_id=payload.plan_id,
            stars_amount=payload.stars_amount,
            telegram_charge_id=payload.telegram_charge_id,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PaymentResponse(
        id=str(payment.id),
        user_id=str(payment.user_id),
        plan=payment.plan,
        stars_amount=payment.stars_amount,
        currency=payment.currency,
        status=payment.status,
        expires_at=payment.expires_at.isoformat() if payment.expires_at else None,
    )


@router.get("/subscription", response_model=PaymentSubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentSubscriptionResponse:
    status_data = await payment_service.check_subscription(current_user, db)
    return PaymentSubscriptionResponse(**status_data)


@router.post("/refund", response_model=PaymentResponse)
async def refund_payment(
    payload: PaymentRefundRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    try:
        payment_id = uuid.UUID(payload.payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nieprawidłowe ID płatności") from exc

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono płatności")

    is_owner = payment.user_id == current_user.id
    is_admin = current_user.role == UserRole.FULL_ACCESS
    if not is_owner and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień do zwrotu")

    try:
        refunded = await payment_service.refund(payment_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PaymentResponse(
        id=str(refunded.id),
        user_id=str(refunded.user_id),
        plan=refunded.plan,
        stars_amount=refunded.stars_amount,
        currency=refunded.currency,
        status=refunded.status,
        expires_at=refunded.expires_at.isoformat() if refunded.expires_at else None,
    )
