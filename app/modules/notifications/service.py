"""Notification module — in-app notifications."""
from __future__ import annotations

import uuid

import streamlit as st
from sqlalchemy import Boolean, ForeignKey, String, Text, select, func
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.shared.base_model import UUIDBase

NOTIF_TYPES = [
    "new_task", "overdue_task", "followup_reminder",
    "referral_reminder", "community_incident", "new_announcement",
]


# ── Model ─────────────────────────────────────────────────────────────────────

class Notification(UUIDBase):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


# ── Service ───────────────────────────────────────────────────────────────────

def create_notification(db: Session, user_id: uuid.UUID | None,
                        notif_type: str, title: str, message: str = "") -> None:
    db.add(Notification(
        user_id=user_id, type=notif_type,
        title=title, message=message,
        created_by="system", updated_by="system",
    ))
    db.commit()


def get_unread_count(db: Session, user_id: uuid.UUID) -> int:
    return db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
    ).scalar() or 0


def mark_all_read(db: Session, user_id: uuid.UUID) -> None:
    notifs = db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
    ).scalars().all()
    for n in notifs:
        n.is_read = True
    db.commit()


# ── Page ─────────────────────────────────────────────────────────────────────

def render_notifications() -> None:
    st.header("🔔 " + t("nav_notifications"))

    user = get_current_user()
    if not user:
        st.warning("Not logged in.")
        return

    col1, col2 = st.columns([4, 1])
    if col2.button("Mark All Read"):
        with get_sync_db() as db:
            mark_all_read(db, user.id)
        st.rerun()

    with get_sync_db() as db:
        notifs = db.execute(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(100)
        ).scalars().all()

    if notifs:
        for n in notifs:
            icon = "🔵" if not n.is_read else "⚪"
            with st.expander(f"{icon} {n.title} — {str(n.created_at)[:16]}"):
                st.write(n.message or "")
                st.caption(f"Type: {n.type}")
    else:
        st.info("No notifications.")
