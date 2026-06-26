import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase


class Task(UUIDBase):
    __tablename__ = "tasks"

    task_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(50), default="home_visit")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)
    due_date: Mapped[str | None] = mapped_column(String(20))
    assigned_to: Mapped[str | None] = mapped_column(String(200))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("citizens.id", ondelete="SET NULL"), nullable=True
    )
    referral_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("referrals.id", ondelete="SET NULL"), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
