from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Payment, User

PLANS: dict[str, dict[str, object]] = {
    "free": {
        "stars": 0,
        "days": 0,
        "tier": "free",
        "label": "Darmowy",
        "description": "Gemini ECO + darmowe modele, limity dzienne",
    },
    "starter": {
        "stars": 50,
        "days": 7,
        "tier": "starter",
        "label": "Starter (7 dni)",
        "description": "SMART bez limitu + GPT-4o 5/dzień",
        "limits": {"smart_unlimited": True, "gpt_daily": 5},
    },
    "pro": {
        "stars": 200,
        "days": 30,
        "tier": "pro",
        "label": "Pro (30 dni)",
        "description": "Wszystkie modele, budżet $2/dzień",
        "limits": {"all_models": True, "daily_usd_cap": 2.0},
    },
    "unlimited": {
        "stars": 500,
        "days": 30,
        "tier": "unlimited",
        "label": "Unlimited (30 dni)",
        "description": "Wszystko + GitHub + budżet $5/dzień",
        "limits": {"all_models": True, "daily_usd_cap": 5.0, "github": True},
    },
}


class PaymentService:
    async def get_plans(self) -> list[dict[str, object]]:
        return [{"id": plan_id, **plan_data} for plan_id, plan_data in PLANS.items()]

    async def create_invoice(self, plan_id: str) -> dict[str, object]:
        if plan_id not in PLANS:
            raise ValueError("Nieprawidłowy plan subskrypcji")
        if plan_id == "free":
            raise ValueError("Plan darmowy nie wymaga płatności")

        plan = PLANS[plan_id]
        return {
            "title": str(plan["label"]),
            "description": str(plan["description"]),
            "currency": "XTR",
            "prices": [{"amount": int(plan["stars"])}],
            "payload": plan_id,
        }

    async def process_payment(
        self,
        user_id: uuid.UUID,
        plan_id: str,
        stars_amount: int,
        telegram_charge_id: str,
        db: AsyncSession,
    ) -> Payment:
        if plan_id not in PLANS or plan_id == "free":
            raise ValueError("Nieprawidłowy plan subskrypcji")
        plan = PLANS[plan_id]

        try:
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                raise ValueError("Nie znaleziono użytkownika")

            now_utc = datetime.now(timezone.utc)
            expires_at = now_utc + timedelta(days=int(plan["days"]))
            payment = Payment(
                user_id=user_id,
                telegram_payment_charge_id=telegram_charge_id,
                plan=plan_id,
                stars_amount=stars_amount,
                currency="XTR",
                status="completed",
                expires_at=expires_at,
            )
            db.add(payment)
            user.subscription_tier = str(plan["tier"])
            user.subscription_expires_at = expires_at
            await db.commit()
            await db.refresh(payment)
            return payment
        except Exception:
            await db.rollback()
            raise

    async def check_subscription(self, user: User, db: AsyncSession) -> dict[str, object | None]:
        now_utc = datetime.now(timezone.utc)
        expires_at = user.subscription_expires_at

        if expires_at is not None and expires_at < now_utc:
            try:
                user.subscription_tier = "free"
                user.subscription_expires_at = None
                await db.commit()
                await db.refresh(user)
            except Exception:
                await db.rollback()
                raise

        active = (
            user.subscription_tier != "free"
            and user.subscription_expires_at is not None
            and user.subscription_expires_at >= now_utc
        )
        tier = user.subscription_tier
        return {
            "active": active,
            "tier": tier,
            "expires_at": user.subscription_expires_at.isoformat()
            if user.subscription_expires_at is not None
            else None,
            "plan_details": PLANS.get(tier),
        }

    async def refund(self, payment_id: uuid.UUID, db: AsyncSession) -> Payment:
        try:
            payment_result = await db.execute(select(Payment).where(Payment.id == payment_id))
            payment = payment_result.scalar_one_or_none()
            if payment is None:
                raise ValueError("Nie znaleziono płatności")

            user_result = await db.execute(select(User).where(User.id == payment.user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                raise ValueError("Nie znaleziono użytkownika")

            payment.status = "refunded"
            user.subscription_tier = "free"
            user.subscription_expires_at = None
            await db.commit()
            await db.refresh(payment)
            return payment
        except Exception:
            await db.rollback()
            raise


payment_service = PaymentService()
