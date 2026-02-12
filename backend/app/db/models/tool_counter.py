from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class ToolCounter(Base):
    __tablename__ = "tool_counters"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_tool_counters_user_id_date"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    grok_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    web_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    smart_credits_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vertex_queries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), default=Decimal("0"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="tool_counters")
