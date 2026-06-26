"""Login History — track login events, sessions, failed attempts."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase


class LoginHistory(UUIDBase):
    __tablename__ = "login_history"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    login_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    logout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    browser: Mapped[str | None] = mapped_column(String(200))
    operating_system: Mapped[str | None] = mapped_column(String(200))
    ip_address: Mapped[str | None] = mapped_column(String(50))
    login_result: Mapped[str] = mapped_column(String(20), default="success")  # success/failed
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
