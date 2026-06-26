"""Versioning — app version info display."""
from __future__ import annotations

import os

import streamlit as st
from app.modules.localization.service import t
from app.shared.enums import UserRole

VERSION_INFO = {
    "version": "2.54",
    "release_date": "2026",
    "environment": os.environ.get("APP_ENV", "production"),
    "description": "Production LTS Release — Population Health Intelligence & Quality Management",
    "modules": [
        "V1: Core Registry",
        "V2: Operations",
        "V2.51: Health Monitoring",
        "V2.53: Population Health Intelligence",
        "V2.54: Production Hardening & Observability",
    ],
}


def render_versioning() -> None:
    st.header("📦 " + t("nav_versioning"))

    col1, col2, col3 = st.columns(3)
    col1.metric("Platform Version", VERSION_INFO["version"])
    col2.metric("Environment", VERSION_INFO["environment"])
    col3.metric("Release", VERSION_INFO["release_date"])

    st.divider()
    st.subheader("Version Description")
    st.write(VERSION_INFO["description"])

    st.subheader("Included Modules")
    for mod in VERSION_INFO["modules"]:
        st.write(f"✅ {mod}")

    st.divider()
    st.subheader("Database Migration Status")
    try:
        from sqlalchemy import text
        from app.core.db_sync import get_sync_db
        with get_sync_db() as db:
            result = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
        st.success(f"Current migration: **{result}**")
    except Exception as e:
        st.error(f"Could not read migration version: {e}")
