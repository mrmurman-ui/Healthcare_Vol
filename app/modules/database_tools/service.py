"""Database Tools — migration history, table stats, index info, DB size."""
from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import text

from app.core.db_sync import get_sync_db
from app.modules.localization.service import t
from app.shared.enums import UserRole

ALL_TABLES = [
    "users", "volunteers", "households", "citizens", "home_visits",
    "referrals", "audit_logs", "tasks", "followups", "notifications",
    "announcements", "community_projects", "health_profiles",
    "health_assessments", "early_warnings", "cvi_scores",
    "quality_indicators", "quality_records", "case_outcomes",
    "risk_scores", "community_scorecards", "performance_metrics",
    "capacity_planning", "system_settings", "feature_flags",
    "app_logs", "system_errors",
]


def render_database_tools() -> None:
    from app.modules.auth.session import assert_roles
    assert_roles(UserRole.SUPER_ADMIN)
    st.header("🗄️ " + t("nav_database_tools"))

    tab1, tab2, tab3 = st.tabs(["Table Statistics", "Migration History", "DB Info"])

    with tab1:
        st.subheader("Record Counts per Table")
        if st.button("🔄 Refresh Stats"):
            st.rerun()

        rows = []
        with get_sync_db() as db:
            for tbl in ALL_TABLES:
                try:
                    count = db.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar() or 0
                    rows.append({"Table": tbl, "Records": count})
                except Exception:
                    rows.append({"Table": tbl, "Records": "N/A"})

        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            total = sum(r["Records"] for r in rows if isinstance(r["Records"], int))
            st.metric("Total Records Across All Tables", f"{total:,}")

    with tab2:
        st.subheader("Alembic Migration History")
        with get_sync_db() as db:
            try:
                result = db.execute(
                    text("SELECT version_num FROM alembic_version")
                ).fetchall()
                current = result[0][0] if result else "Unknown"
                st.metric("Current Migration Version", current)

                migrations = [
                    ("0001", "V1 — Initial schema (users, volunteers, households, citizens, home_visits, referrals, audit_logs)"),
                    ("0002", "V2 — Operations (tasks, followups, notifications, announcements, community_projects)"),
                    ("0003", "V2.51 — Health monitoring (health_profiles, health_assessments, early_warnings, cvi_scores)"),
                    ("0004", "V2.53 — Population health (quality_indicators, quality_records, case_outcomes, risk_scores, community_scorecards, performance_metrics, capacity_planning)"),
                    ("0005", "V2.54 — Production hardening (system_settings, feature_flags, app_logs, system_errors)"),
                ]
                for rev, desc in migrations:
                    icon = "✅" if current >= rev else "⏳"
                    st.write(f"{icon} **{rev}** — {desc}")
            except Exception as e:
                st.error(f"Could not read migration history: {e}")

    with tab3:
        st.subheader("Database Information")
        with get_sync_db() as db:
            try:
                ver = db.execute(text("SELECT version()")).scalar()
                st.write(f"**PostgreSQL Version:** {ver}")

                try:
                    db_size = db.execute(text(
                        "SELECT pg_size_pretty(pg_database_size(current_database()))"
                    )).scalar()
                    st.metric("Database Size", db_size)
                except Exception:
                    st.info("Database size: not available")

                try:
                    table_sizes = db.execute(text("""
                        SELECT tablename,
                               pg_size_pretty(pg_total_relation_size(quote_ident(tablename))) as size
                        FROM pg_tables
                        WHERE schemaname = 'public'
                        ORDER BY pg_total_relation_size(quote_ident(tablename)) DESC
                        LIMIT 15
                    """)).fetchall()
                    if table_sizes:
                        size_df = pd.DataFrame(table_sizes, columns=["Table", "Size"])
                        st.subheader("Table Sizes")
                        st.dataframe(size_df, use_container_width=True, hide_index=True)
                except Exception:
                    pass

            except Exception as e:
                st.error(f"Database query error: {e}")
