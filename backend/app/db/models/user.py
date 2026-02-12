from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, enum.Enum):
    DEMO = 'DEMO'
    FULL_ACCESS = 'FULL_ACCESS'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name='user_role', create_constraint=True),
        nullable=False,
        default=UserRole.DEMO,
    )
    authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    default_mode: Mapped[str] = mapped_column(String(10), default='eco')
    settings_: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, server_default='{}')
    subscription_tier: Mapped[str] = mapped_column(String(20), default='free')
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
