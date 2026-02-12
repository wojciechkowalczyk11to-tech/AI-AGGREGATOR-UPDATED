from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.db.models.user import User, UserRole
from app.db.session import get_session_factory
from sqlalchemy import select


def parse_ids(raw_value: str) -> list[int]:
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


async def seed_users() -> None:
    settings = get_settings()
    session_factory = get_session_factory()

    full_ids = parse_ids(settings.FULL_TELEGRAM_IDS)
    demo_ids = parse_ids(settings.DEMO_TELEGRAM_IDS)

    async with session_factory() as session:
        for telegram_id in full_ids:
            existing = await session.execute(select(User).where(User.telegram_id == telegram_id))
            if existing.scalar_one_or_none() is None:
                session.add(User(telegram_id=telegram_id, role=UserRole.FULL_ACCESS, authorized=True))

        for telegram_id in demo_ids:
            existing = await session.execute(select(User).where(User.telegram_id == telegram_id))
            if existing.scalar_one_or_none() is None:
                session.add(User(telegram_id=telegram_id, role=UserRole.DEMO, authorized=False))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_users())
