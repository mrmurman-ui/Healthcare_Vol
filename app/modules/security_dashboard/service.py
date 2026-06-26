"""Security Dashboard — users, roles, failed logins, activity monitoring."""
from __future__ import annotations

import plotly.express as px
import streamlit as st
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
from app.modules.login_history.model import LoginHistory
from app.modules.roles.model import Role, UserRole
from app.modules.user_management.model import UserProfile, USER_STATUS_LOCKED
from app.modules.users.model import User


def render_security_dashboard() -> None:
    from app.modules.permissions.service import require_permission
    require_permission("administration", "VIEW")

    st.header("🔒 Security Dashboard")

    with get_sync_db() as db:
        total_users = db.execute(select(func.count()).select_from(User)).scalar() or 0
        active_users = db.execute(
            select(func.count()).select_from(User).where(User.is_active == True)
        ).scalar() or 0
        inactive_users = total_users - active_users

        # Failed logins (last 24h)
        try:
            failed_logins = db.execute(
                select(func.count()).select_from(LoginHistory)
                .where(LoginHistory.login_result == "failed")
            ).scalar() or 0
        except Exception:
            failed_logins = 0

        # Role distribution
        try:
            role_dist = db.execute(
                select(User.role, func.count()).group_by(User.role)
            ).all()
        except Exception:
            role_dist = []

        # Recent logins
        try:
            recent_logins = db.execute(
                select(LoginHistory)
                .order_by(LoginHistory.login_time.desc())
                .limit(10)
            ).scalars().all()
        except Exception:
            recent_logins = []

    # ── KPIs ─────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Users", total_users)
    c2.metric("Active Users", active_users)
    c3.metric("Inactive Users", inactive_users)
    c4.metric("Failed Logins", failed_logins,
              delta=None if failed_logins == 0 else f"{failed_logins} failures",
              delta_color="inverse")

    st.divider()

    col1, col2 = st.columns(2)

    # Role distribution chart
    if role_dist:
        fig = px.pie(
            names=[r[0] for r in role_dist],
            values=[r[1] for r in role_dist],
            title="User Role Distribution",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        col1.plotly_chart(fig, use_container_width=True)

    # Active vs inactive
    fig2 = px.bar(
        x=["Active", "Inactive"],
        y=[active_users, inactive_users],
        title="User Status",
        color=["Active", "Inactive"],
        color_discrete_map={"Active": "#2a9d8f", "Inactive": "#e63946"},
    )
    col2.plotly_chart(fig2, use_container_width=True)

    # Recent logins
    st.subheader("Recent Login Activity")
    if recent_logins:
        import pandas as pd
        df = pd.DataFrame([{
            "User": l.username,
            "Time": str(l.login_time or "")[:19],
            "Result": "Success" if l.login_result == "success" else "FAILED",
            "IP": l.ip_address or "",
            "Browser": l.browser or "",
        } for l in recent_logins])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No login history yet.")

    st.divider()
    st.subheader("Configured Roles")
    with get_sync_db() as db:
        roles = db.execute(
            select(Role).where(Role.is_deleted == False)
        ).scalars().all()

    if roles:
        import pandas as pd
        df2 = pd.DataFrame([{
            "Code": r.role_code,
            "Thai": r.role_name_th,
            "English": r.role_name_en,
        } for r in roles])
        st.dataframe(df2, use_container_width=True, hide_index=True)
