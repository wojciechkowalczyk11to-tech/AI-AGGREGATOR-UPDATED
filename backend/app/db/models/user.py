from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, JSON, String
from sqlalchemy import Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.ledger import UsageLedger
    from app.db.models.payment import Payment
    from app.db.models.rag_item import RagItem
    from app.db.models.session import ChatSession
    from app.db.models.tool_counter import ToolCounter
    from app.db.models.user_memory import UserMemory


class UserRole(str, enum.Enum):
    DEMO = "DEMO"
    FULL_ACCESS = "FULL_ACCESS"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_telegram_id", "telegram_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.DEMO,
        nullable=False,
    )
    authorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_mode: Mapped[str] = mapped_column(String(10), default="eco", nullable=False)
    settings_: Mapped[dict[str, Any]] = mapped_column(
        "settings", JSON, default=dict, nullable=False
    )
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    subscription_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    usage_ledgers: Mapped[list["UsageLedger"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tool_counters: Mapped[list["ToolCounter"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    rag_items: Mapped[list["RagItem"]] = relationship(back_populates="user")
    memories: Mapped[list["UserMemory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
