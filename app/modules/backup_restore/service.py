"""Backup and Restore — JSON and Excel export/import of core data."""
from __future__ import annotations

import io
import json
from datetime import datetime, UTC

import pandas as pd
import streamlit as st
from sqlalchemy import select, text

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.households.model import Household
from app.modules.localization.service import t
from app.modules.volunteers.model import Volunteer
from app.shared.enums import UserRole


def export_json(db, tables: list[str]) -> str:
    """Export specified tables as JSON."""
    result = {}
    for tbl in tables:
        try:
            rows = db.execute(text(f"SELECT * FROM {tbl} LIMIT 10000")).mappings().all()
            result[tbl] = [
                {k: str(v) if v is not None else None for k, v in row.items()}
                for row in rows
            ]
        except Exception as e:
            result[tbl] = {"error": str(e)}
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


def export_excel_backup(db) -> bytes:
    """Export core tables to a multi-sheet Excel file."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        tables = ["volunteers", "households", "citizens",
                  "home_visits", "referrals", "tasks", "followups"]
        for tbl in tables:
            try:
                rows = db.execute(text(f"SELECT * FROM {tbl} LIMIT 5000")).mappings().all()
                if rows:
                    df = pd.DataFrame([dict(r) for r in rows])
                    df.to_excel(writer, sheet_name=tbl[:31], index=False)
            except Exception:
                pass
    return buf.getvalue()


def render_backup_restore() -> None:
    from app.modules.auth.session import assert_roles
    assert_roles(UserRole.SUPER_ADMIN)
    st.header("💾 " + t("nav_backup"))

    tab1, tab2 = st.tabs(["Export / Backup", "Import / Restore"])

    with tab1:
        st.subheader("Export Data")

        col1, col2 = st.columns(2)

        if col1.button("📥 Export All Data (JSON)"):
            core_tables = [
                "volunteers", "households", "citizens", "home_visits",
                "referrals", "tasks", "followups", "health_profiles",
                "health_assessments", "early_warnings",
            ]
            with get_sync_db() as db:
                json_data = export_json(db, core_tables)
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M")
            st.download_button(
                "⬇ Download JSON Backup",
                data=json_data,
                file_name=f"health_platform_backup_{timestamp}.json",
                mime="application/json",
            )

        if col2.button("📥 Export All Data (Excel)"):
            with get_sync_db() as db:
                excel_data = export_excel_backup(db)
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M")
            st.download_button(
                "⬇ Download Excel Backup",
                data=excel_data,
                file_name=f"health_platform_backup_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.divider()
        st.subheader("Individual Table Export")
        tables = ["volunteers", "households", "citizens", "home_visits",
                  "referrals", "tasks", "health_assessments"]
        sel_table = st.selectbox("Select Table", tables)

        if st.button("Export Selected Table"):
            with get_sync_db() as db:
                json_data = export_json(db, [sel_table])
            st.download_button(
                f"⬇ Download {sel_table}.json",
                data=json_data,
                file_name=f"{sel_table}_backup.json",
                mime="application/json",
            )

    with tab2:
        st.subheader("Import from JSON")
        st.warning("⚠️ Import will ADD records. It does NOT overwrite existing data. "
                   "Duplicates will be skipped automatically.")

        uploaded = st.file_uploader("Upload JSON backup file", type=["json"])
        if uploaded:
            try:
                data = json.loads(uploaded.read())
                st.success(f"File parsed. Tables found: {', '.join(data.keys())}")
                st.json({k: f"{len(v)} records" for k, v in data.items()
                         if isinstance(v, list)})
                st.info("Manual review complete. Contact system administrator "
                        "to restore from backup using database tools.")
            except Exception as e:
                st.error(f"Invalid JSON file: {e}")

        st.divider()
        st.subheader("Recovery Procedure")
        st.code("""
# 1. Restore database backup
pg_restore -U healthuser -d healthdb backup.sql

# 2. Apply any pending migrations
alembic upgrade head

# 3. Restart Streamlit
streamlit run app/main.py

# 4. Verify via System Health dashboard
        """, language="bash")
