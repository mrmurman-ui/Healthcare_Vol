"""Feature Flags — runtime enable/disable without code changes."""
from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import Boolean, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.shared.base_model import UUIDBase
from app.shared.enums import UserRole

DEFAULT_FLAGS: list[dict] = [
    {"key": "ai_assistant",  "name": "AI Assistant",        "default": True},
    {"key": "forecasting",   "name": "Forecast Analytics",  "default": True},
    {"key": "gis",           "name": "GIS / Maps",          "default": True},
    {"key": "notifications", "name": "Notifications",       "default": True},
    {"key": "analytics",     "name": "Analytics",           "default": True},
    {"key": "heatmaps",      "name": "Heatmaps",            "default": True},
    {"key": "exports",       "name": "Export Engine",       "default": True},
    {"key": "reports",       "name": "Reports",             "default": True},
    {"key": "campaigns",     "name": "Campaigns",           "default": False},
    {"key": "care_plans",    "name": "Care Plans",          "default": False},
    {"key": "scheduler",     "name": "Job Scheduler",       "default": True},
    {"key": "import_engine", "name": "Import Engine",       "default": True},
]


class FeatureFlag(UUIDBase):
    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


def is_enabled(key: str) -> bool:
    """Check if a feature flag is enabled. Defaults to True if not found."""
    try:
        with get_sync_db() as db:
            flag = db.execute(
                select(FeatureFlag).where(FeatureFlag.key == key,
                                           FeatureFlag.is_deleted == False)
            ).scalar_one_or_none()
            return flag.enabled if flag else True
    except Exception:
        return True


def seed_flags(db: Session) -> None:
    for f in DEFAULT_FLAGS:
        existing = db.execute(
            select(FeatureFlag).where(FeatureFlag.key == f["key"])
        ).scalar_one_or_none()
        if not existing:
            db.add(FeatureFlag(
                key=f["key"], name=f["name"],
                enabled=f["default"],
                created_by="system", updated_by="system",
            ))
    db.commit()


def render_feature_flags() -> None:
    from app.modules.auth.session import assert_roles
    assert_roles(UserRole.SUPER_ADMIN)
    st.header("🚩 " + t("nav_feature_flags"))

    with get_sync_db() as db:
        seed_flags(db)
        flags = db.execute(
            select(FeatureFlag).where(FeatureFlag.is_deleted == False)
            .order_by(FeatureFlag.name)
        ).scalars().all()

    user = get_current_user()
    actor = user.email if user else "system"

    st.info("Toggle features on/off without restarting the application.")

    if flags:
        for flag in flags:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{flag.name}**")
            col2.write("🟢 On" if flag.enabled else "🔴 Off")
            if col3.button("Toggle", key=f"flag_{flag.key}"):
                with get_sync_db() as db:
                    f = db.execute(
                        select(FeatureFlag).where(FeatureFlag.key == flag.key)
                    ).scalar_one_or_none()
                    if f:
                        f.enabled = not f.enabled
                        f.updated_by = actor
                st.rerun()

        st.divider()
        df = pd.DataFrame([{
            "Key": f.key, "Feature": f.name,
            "Status": "✅ Enabled" if f.enabled else "❌ Disabled",
        } for f in flags])
        st.dataframe(df, use_container_width=True, hide_index=True)
