"""Error Tracking — system error capture and admin dashboard."""
from __future__ import annotations

import traceback
from datetime import datetime, UTC

import pandas as pd
import streamlit as st
from sqlalchemy import Boolean, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_sync import get_sync_db
from app.modules.localization.service import t
from app.shared.base_model import UUIDBase
from app.shared.enums import UserRole

SEVERITY_LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]


class SystemError(UUIDBase):
    __tablename__ = "system_errors"

    level: Mapped[str] = mapped_column(String(20), default="ERROR", index=True)
    module: Mapped[str] = mapped_column(String(100), index=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    traceback_text: Mapped[str | None] = mapped_column(Text)
    user_email: Mapped[str | None] = mapped_column(String(255))
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


def capture_error(module: str, message: str, exc: Exception | None = None,
                  level: str = "ERROR") -> None:
    """Capture and store an error. Safe to call in except blocks."""
    try:
        from app.modules.auth.session import get_current_user
        user = get_current_user()
        actor = user.email if user else "system"
        tb = traceback.format_exc() if exc else None
        with get_sync_db() as db:
            db.add(SystemError(
                level=level, module=module, message=message[:500],
                traceback_text=tb, user_email=actor,
                created_by=actor, updated_by=actor,
            ))
    except Exception:
        pass  # error tracking must never crash the app


def render_error_tracking() -> None:
    from app.modules.auth.session import assert_roles
    assert_roles(UserRole.SUPER_ADMIN, UserRole.PROVINCE_ADMIN)
    st.header("🐛 " + t("nav_error_tracking"))

    with get_sync_db() as db:
        stats = db.execute(
            select(SystemError.level, func.count())
            .where(SystemError.is_deleted == False, SystemError.resolved == False)
            .group_by(SystemError.level)
        ).all()
        stat_map = {r[0]: r[1] for r in stats}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🚨 Critical (open)", stat_map.get("CRITICAL", 0))
    c2.metric("🔴 Error (open)", stat_map.get("ERROR", 0))
    c3.metric("🟡 Warning (open)", stat_map.get("WARNING", 0))
    c4.metric("🔵 Info (open)", stat_map.get("INFO", 0))

    col1, col2, col3 = st.columns(3)
    level_f = col1.selectbox("Level", [""] + SEVERITY_LEVELS)
    resolved_f = col2.selectbox("Status", ["", "open", "resolved"])
    limit = col3.selectbox("Limit", [50, 100, 200], index=0)

    with get_sync_db() as db:
        stmt = select(SystemError).where(SystemError.is_deleted == False)
        if level_f:
            stmt = stmt.where(SystemError.level == level_f)
        if resolved_f == "open":
            stmt = stmt.where(SystemError.resolved == False)
        elif resolved_f == "resolved":
            stmt = stmt.where(SystemError.resolved == True)
        stmt = stmt.order_by(SystemError.created_at.desc()).limit(limit)
        errors = db.execute(stmt).scalars().all()

    if errors:
        df = pd.DataFrame([{
            "Time": str(e.created_at)[:19],
            "Level": e.level,
            "Module": e.module,
            "Message": e.message[:100],
            "User": e.user_email or "",
            "Resolved": "✅" if e.resolved else "❌",
        } for e in errors])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        with st.expander("✏️ Resolve Error"):
            open_errors = [e for e in errors if not e.resolved]
            if open_errors:
                opts = {f"{e.level} — {e.message[:60]}": e.id for e in open_errors}
                sel = st.selectbox("Select Error", list(opts.keys()))
                note = st.text_area("Resolution Notes")
                if st.button("Mark Resolved"):
                    from app.modules.auth.session import get_current_user
                    user = get_current_user()
                    actor = user.email if user else "system"
                    with get_sync_db() as db:
                        err = db.get(SystemError, opts[sel])
                        if err:
                            err.resolved = True
                            err.resolved_by = actor
                            err.notes = note
                            err.updated_by = actor
                    st.success("Error marked resolved.")
                    st.rerun()
    else:
        st.info("No errors found.")
