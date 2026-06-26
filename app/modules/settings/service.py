"""Settings module — editable system configuration for administrators."""
from __future__ import annotations

import streamlit as st
from sqlalchemy import Boolean, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.shared.base_model import UUIDBase
from app.shared.enums import UserRole

# Default settings
DEFAULTS: dict[str, str] = {
    "app_name": "AI Community Health & Volunteer Operations Platform",
    "org_name": "Community Health Organization",
    "timezone": "Asia/Bangkok",
    "language": "th",
    "theme": "light",
    "maintenance_mode": "false",
    "session_timeout_minutes": "60",
    "min_password_length": "8",
    "max_upload_mb": "10",
    "map_center_lat": "13.7563",
    "map_center_lon": "100.5018",
    "pagination_size": "50",
    "ai_daily_limit": "100",
    "max_login_attempts": "5",
    "lockout_minutes": "15",
}


class SystemSetting(UUIDBase):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(String(300))
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


# ── Service ───────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    try:
        with get_sync_db() as db:
            row = db.execute(
                select(SystemSetting).where(SystemSetting.key == key,
                                             SystemSetting.is_deleted == False)
            ).scalar_one_or_none()
            return row.value if row and row.value is not None else default
    except Exception:
        return default


def set_setting(key: str, value: str, actor: str = "system",
                description: str = "") -> None:
    with get_sync_db() as db:
        row = db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        ).scalar_one_or_none()
        if row:
            row.value = value
            row.updated_by = actor
        else:
            db.add(SystemSetting(
                key=key, value=value, description=description,
                created_by=actor, updated_by=actor,
            ))


def seed_default_settings(db: Session) -> None:
    for key, value in DEFAULTS.items():
        existing = db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        ).scalar_one_or_none()
        if not existing:
            db.add(SystemSetting(
                key=key, value=value,
                created_by="system", updated_by="system",
            ))
    db.commit()


# ── Page ─────────────────────────────────────────────────────────────────────

def render_settings() -> None:
    from app.modules.auth.session import assert_roles
    assert_roles(UserRole.SUPER_ADMIN, UserRole.PROVINCE_ADMIN)
    st.header("⚙️ " + t("nav_settings"))

    with get_sync_db() as db:
        seed_default_settings(db)
        all_settings = db.execute(
            select(SystemSetting).where(SystemSetting.is_deleted == False)
            .order_by(SystemSetting.key)
        ).scalars().all()

    user = get_current_user()
    actor = user.email if user else "system"

    tab1, tab2 = st.tabs(["General Settings", "Security Settings"])

    with tab1:
        with st.form("general_settings"):
            current = {s.key: s.value or "" for s in all_settings}
            app_name = st.text_input("Application Name",
                                      value=current.get("app_name", DEFAULTS["app_name"]))
            org_name = st.text_input("Organization Name",
                                      value=current.get("org_name", DEFAULTS["org_name"]))
            tz = st.selectbox("Timezone",
                               ["Asia/Bangkok", "Asia/Tokyo", "UTC", "Europe/London"],
                               index=0)
            map_lat = st.number_input("Map Center Latitude",
                                       value=float(current.get("map_center_lat", "13.7563")),
                                       format="%.4f")
            map_lon = st.number_input("Map Center Longitude",
                                       value=float(current.get("map_center_lon", "100.5018")),
                                       format="%.4f")
            pagination = st.number_input("Records Per Page",
                                          min_value=10, max_value=500,
                                          value=int(current.get("pagination_size", "50")))
            maintenance = st.checkbox("Maintenance Mode",
                                       value=current.get("maintenance_mode") == "true")
            ai_limit = st.number_input("AI Daily Usage Limit (per user)",
                                        min_value=10, max_value=1000,
                                        value=int(current.get("ai_daily_limit", "100")))
            saved = st.form_submit_button("💾 Save Settings")

        if saved:
            updates = {
                "app_name": app_name, "org_name": org_name,
                "timezone": tz,
                "map_center_lat": str(map_lat), "map_center_lon": str(map_lon),
                "pagination_size": str(pagination),
                "maintenance_mode": "true" if maintenance else "false",
                "ai_daily_limit": str(ai_limit),
            }
            for k, v in updates.items():
                set_setting(k, v, actor)
            st.success("Settings saved.")
            st.rerun()

    with tab2:
        with st.form("security_settings"):
            current = {s.key: s.value or "" for s in all_settings}
            min_pwd = st.number_input("Minimum Password Length",
                                       min_value=6, max_value=32,
                                       value=int(current.get("min_password_length", "8")))
            session_timeout = st.number_input("Session Timeout (minutes)",
                                               min_value=5, max_value=1440,
                                               value=int(current.get("session_timeout_minutes", "60")))
            max_attempts = st.number_input("Max Login Attempts",
                                            min_value=3, max_value=20,
                                            value=int(current.get("max_login_attempts", "5")))
            lockout = st.number_input("Lockout Duration (minutes)",
                                       min_value=1, max_value=1440,
                                       value=int(current.get("lockout_minutes", "15")))
            max_upload = st.number_input("Max Upload Size (MB)",
                                          min_value=1, max_value=100,
                                          value=int(current.get("max_upload_mb", "10")))
            saved2 = st.form_submit_button("💾 Save Security Settings")

        if saved2:
            updates2 = {
                "min_password_length": str(min_pwd),
                "session_timeout_minutes": str(session_timeout),
                "max_login_attempts": str(max_attempts),
                "lockout_minutes": str(lockout),
                "max_upload_mb": str(max_upload),
            }
            for k, v in updates2.items():
                set_setting(k, v, actor)
            st.success("Security settings saved.")
            st.rerun()
