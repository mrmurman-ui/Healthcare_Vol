import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.core.db_sync import get_sync_db
from app.modules.audit.service import AuditLog
from app.modules.auth.session import assert_roles
from app.modules.localization.service import t
from app.shared.enums import UserRole


def render_audit() -> None:
    assert_roles(UserRole.SUPER_ADMIN, UserRole.PROVINCE_ADMIN)
    st.header(t("nav_audit"))

    with get_sync_db() as db:
        logs = db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)
        ).scalars().all()

    if logs:
        df = pd.DataFrame([{
            "Time": str(log.created_at)[:19],
            "Actor": log.actor,
            "Action": log.action,
            "Resource": log.resource_type,
            "ID": log.resource_id or "",
            "Detail": (log.detail or "")[:100],
        } for log in logs])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No audit entries.")
