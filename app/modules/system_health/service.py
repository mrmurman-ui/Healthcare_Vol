"""System Health — real-time platform health dashboard."""
from __future__ import annotations

import platform
import time
from datetime import datetime, UTC

import streamlit as st
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
from app.modules.error_tracking.service import SystemError
from app.modules.localization.service import t
from app.modules.versioning.service import VERSION_INFO
from app.shared.enums import UserRole


def check_db_connection() -> tuple[bool, float]:
    """Returns (is_connected, response_time_ms)."""
    try:
        start = time.time()
        with get_sync_db() as db:
            db.execute(text("SELECT 1"))
        ms = round((time.time() - start) * 1000, 1)
        return True, ms
    except Exception:
        return False, -1.0


def get_table_counts() -> dict[str, int]:
    tables = ["users", "volunteers", "households", "citizens",
              "home_visits", "referrals", "health_assessments",
              "tasks", "followups", "early_warnings"]
    counts = {}
    try:
        with get_sync_db() as db:
            for tbl in tables:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
                    counts[tbl] = int(result or 0)
                except Exception:
                    counts[tbl] = -1
    except Exception:
        pass
    return counts


def render_system_health() -> None:
    from app.modules.auth.session import assert_roles
    assert_roles(UserRole.SUPER_ADMIN, UserRole.PROVINCE_ADMIN)
    st.header("💚 " + t("nav_system_health"))

    if st.button("🔄 Refresh"):
        st.rerun()

    # DB connectivity
    db_ok, db_ms = check_db_connection()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🗄️ Database",
                "✅ Connected" if db_ok else "❌ Disconnected",
                f"{db_ms}ms" if db_ok else "—")
    col2.metric("🐍 Python", platform.python_version())
    col3.metric("🖥️ Platform", platform.system())
    col4.metric("📦 App Version", VERSION_INFO.get("version", "2.54"))

    st.divider()
    st.subheader("Application Version")
    col1, col2, col3 = st.columns(3)
    col1.metric("Version", VERSION_INFO.get("version", "2.54"))
    col2.metric("Release Date", VERSION_INFO.get("release_date", "2026"))
    col3.metric("Environment", VERSION_INFO.get("environment", "production"))

    st.divider()
    st.subheader("Database Response Time")
    if db_ok:
        if db_ms < 100:
            st.success(f"✅ Excellent: {db_ms}ms")
        elif db_ms < 500:
            st.warning(f"⚠️ Acceptable: {db_ms}ms")
        else:
            st.error(f"❌ Slow: {db_ms}ms — check connection")
    else:
        st.error("❌ Database connection failed")

    st.divider()
    st.subheader("Record Counts")
    counts = get_table_counts()
    if counts:
        cols = st.columns(5)
        for i, (tbl, cnt) in enumerate(counts.items()):
            cols[i % 5].metric(tbl.replace("_", " ").title(), cnt if cnt >= 0 else "Error")

    st.divider()
    st.subheader("Recent Errors")
    with get_sync_db() as db:
        recent_errors = db.execute(
            select(SystemError)
            .where(SystemError.resolved == False, SystemError.is_deleted == False)
            .order_by(SystemError.created_at.desc())
            .limit(5)
        ).scalars().all()
        error_count = db.execute(
            select(func.count()).select_from(SystemError)
            .where(SystemError.resolved == False)
        ).scalar() or 0

    st.metric("Open Errors", error_count)
    for err in recent_errors:
        level_icon = {"CRITICAL": "🚨", "ERROR": "🔴", "WARNING": "🟡"}.get(err.level, "🔵")
        st.write(f"{level_icon} [{err.level}] {err.module} — {err.message[:80]}")

    # Demo loader section
    render_demo_loader()


def render_demo_loader() -> None:
    """In-app demo data loader — callable from System Health page."""
    st.divider()
    st.subheader("🎮 Demo Data")
    st.caption("Load realistic Thai community health data to explore all platform features.")

    col1, col2 = st.columns([2, 3])
    col2.markdown("""
    **What gets loaded:**
    - 5 users (all roles) · 30 volunteers · 80 households · 300 citizens
    - 180 health profiles · 400+ assessments · 400 home visits
    - 80 referrals · 60 tasks · 50 follow-ups · 50 early warnings
    - Community scorecards · Quality indicators · Performance metrics
    - Announcements · Notifications · Risk scores · Case outcomes
    """)

    if col1.button("🚀 Load Demo Data", type="primary", use_container_width=True):
        import subprocess, sys
        with st.spinner("Loading demo data — this takes about 30 seconds..."):
            result = subprocess.run(
                [sys.executable, "scripts/demo_data.py"],
                capture_output=True, text=True, timeout=180
            )
        if result.returncode == 0:
            st.success("✅ Demo data loaded! Refresh any page to see the data.")
            st.code(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        else:
            # Show both stdout and stderr for debugging
            st.error("Failed to load demo data.")
            if result.stdout:
                st.code(result.stdout[-500:])
            if result.stderr:
                st.code(result.stderr[-1000:])
