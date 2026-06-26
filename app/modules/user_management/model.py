"""Enhanced User model — full profile, status, soft-delete."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import UUIDBase

USER_STATUS_ACTIVE    = "active"
USER_STATUS_INACTIVE  = "inactive"
USER_STATUS_SUSPENDED = "suspended"
USER_STATUS_LOCKED    = "locked"
USER_STATUS_DELETED   = "deleted"

ALL_STATUSES = [USER_STATUS_ACTIVE, USER_STATUS_INACTIVE,
                USER_STATUS_SUSPENDED, USER_STATUS_LOCKED]


class UserProfile(UUIDBase):
    """Extended profile fields — supplements the base User model."""
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    user_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    first_name_th: Mapped[str | None] = mapped_column(String(100))
    last_name_th: Mapped[str | None] = mapped_column(String(100))
    first_name_en: Mapped[str | None] = mapped_column(String(100))
    last_name_en: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    profile_photo: Mapped[str | None] = mapped_column(String(500))
    organization: Mapped[str | None] = mapped_column(String(200))
    position: Mapped[str | None] = mapped_column(String(200))
    license_number: Mapped[str | None] = mapped_column(String(100))
    volunteer_code: Mapped[str | None] = mapped_column(String(50))
    advisor_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    community_leader_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default=USER_STATUS_ACTIVE, index=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_login_count: Mapped[int] = mapped_column(default=0)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[str | None] = mapped_column(String(200))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
