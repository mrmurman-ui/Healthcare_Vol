"""Application Logs — structured event logging for all user actions."""
from __future__ import annotations

import json
from datetime import datetime, UTC

import pandas as pd
import streamlit as st
from sqlalchemy import String, Text, select, text
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.shared.base_model import UUIDBase
from app.shared.enums import UserRole


def _t(th: str, en: str) -> str:
    return th if st.session_state.get("lang", "TH") == "TH" else en


LOG_LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_MODULES = [
    "auth", "volunteers", "households", "citizens", "home_visits",
    "referrals", "tasks", "health_profiles", "health_assessments",
    "ai_assistant", "reports", "import", "export", "scheduler", "system",
]


class AppLog(UUIDBase):
    __tablename__ = "app_logs"

    level: Mapped[str] = mapped_column(String(20), default="INFO", index=True)
    module: Mapped[str] = mapped_column(String(100), index=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    user_email: Mapped[str | None] = mapped_column(String(255))
    # log_metadata omitted — column may not exist in older DB schemas
    is_deleted: Mapped[bool] = mapped_column(default=False)


def log_event(module: str, action: str, level: str = "INFO",
              metadata: dict | None = None) -> None:
    """Write a structured log entry. Safe to call anywhere — never raises."""
    try:
        from app.modules.auth.session import get_current_user as _get_user
        user = _get_user()
        actor = user.email if user else "system"
        # Use raw SQL to avoid column-mismatch errors on older DB schemas
        with get_sync_db() as db:
            # Try with log_metadata first; fall back to without
            try:
                db.execute(text("""
                    INSERT INTO app_logs
                        (id, level, module, action, user_email, log_metadata,
                         is_deleted, created_at, updated_at, created_by, updated_by)
                    VALUES
                        (gen_random_uuid(), :level, :module, :action, :user_email,
                         :metadata, false, NOW(), NOW(), :actor, :actor)
                """), {
                    "level": level, "module": module, "action": action,
                    "user_email": actor,
                    "metadata": json.dumps(metadata) if metadata else None,
                    "actor": actor,
                })
            except Exception:
                # Fallback: no log_metadata column
                db.execute(text("""
                    INSERT INTO app_logs
                        (id, level, module, action, user_email,
                         is_deleted, created_at, updated_at, created_by, updated_by)
                    VALUES
                        (gen_random_uuid(), :level, :module, :action, :user_email,
                         false, NOW(), NOW(), :actor, :actor)
                """), {
                    "level": level, "module": module, "action": action,
                    "user_email": actor, "actor": actor,
                })
    except Exception:
        pass  # logging must never crash the app


def render_application_logs() -> None:
    from app.modules.auth.session import assert_roles
    assert_roles(UserRole.SUPER_ADMIN, UserRole.PROVINCE_ADMIN)
    st.header("📜 " + t("nav_app_logs"))

    col1, col2, col3 = st.columns(3)
    level_filter  = col1.selectbox(_t("ระดับ", "Level"),  [""] + LOG_LEVELS)
    module_filter = col2.selectbox(_t("โมดูล", "Module"), [""] + LOG_MODULES)
    limit         = col3.selectbox(_t("แสดงล่าสุด", "Show Last"), [50, 100, 200, 500], index=1)

    # Use raw SQL to select only columns that are guaranteed to exist
    try:
        with get_sync_db() as db:
            # Detect whether log_metadata column exists
            col_check = db.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'app_logs' AND column_name = 'log_metadata'
            """)).fetchone()
            has_metadata = col_check is not None

            meta_col = ", log_metadata" if has_metadata else ", NULL as log_metadata"
            where_parts = ["is_deleted = false"]
            params: dict = {"limit": int(limit)}

            if level_filter:
                where_parts.append("level = :level")
                params["level"] = level_filter
            if module_filter:
                where_parts.append("module = :module")
                params["module"] = module_filter

            where_sql = " AND ".join(where_parts)
            rows = db.execute(text(f"""
                SELECT level, module, action, user_email{meta_col},
                       created_at
                FROM app_logs
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT :limit
            """), params).fetchall()

    except Exception as e:
        st.error(_t(f"เกิดข้อผิดพลาดในการโหลด Logs: {e}",
                    f"Error loading logs: {e}"))
        return

    level_icons = {"INFO": "🔵", "WARNING": "🟡", "ERROR": "🔴", "CRITICAL": "🚨"}

    if rows:
        from collections import Counter
        counts = Counter(r[0] for r in rows)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔵 INFO",     counts.get("INFO", 0))
        c2.metric("🟡 WARNING",  counts.get("WARNING", 0))
        c3.metric("🔴 ERROR",    counts.get("ERROR", 0))
        c4.metric("🚨 CRITICAL", counts.get("CRITICAL", 0))

        df = pd.DataFrame([{
            _t("เวลา",    "Time"):    str(r[5])[:19] if r[5] else "",
            _t("ระดับ",   "Level"):   level_icons.get(r[0], "") + " " + (r[0] or ""),
            _t("โมดูล",   "Module"):  r[1] or "",
            _t("การกระทำ","Action"):  r[2] or "",
            _t("ผู้ใช้",  "User"):    r[3] or "",
            _t("ข้อมูล",  "Metadata"): (r[4] or "")[:80],
        } for r in rows])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(_t("ไม่พบรายการ Log", "No log entries found."))
