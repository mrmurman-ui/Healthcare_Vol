"""Executive Command Center — strategic overview for administrators and officers."""
from __future__ import annotations

import plotly.express as px
import streamlit as st
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
from app.modules.citizens.model import Citizen
from app.modules.community_scorecards.service import CommunityScorecard
from app.modules.early_warning.model import EarlyWarning
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.modules.referrals.model import Referral
from app.modules.risk_stratification.service import RiskScore
from app.modules.tasks.model import Task
from app.modules.volunteers.model import Volunteer
import sqlalchemy as sa


def render_executive_command_center() -> None:
    st.header("🎯 " + t("nav_executive"))
    st.caption("Executive governance dashboard — no clinical recommendations.")

    with get_sync_db() as db:
        total_citizens = db.execute(select(func.count()).select_from(Citizen)).scalar() or 0
        total_vols = db.execute(select(func.count()).select_from(Volunteer)).scalar() or 0
        active_vols = db.execute(
            select(func.count()).select_from(Volunteer)
            .where(Volunteer.status == "active")
        ).scalar() or 0

        cit_row = db.execute(
            select(
                func.sum(Citizen.is_elderly.cast(sa.Integer)).label("elderly"),
                func.sum(Citizen.is_disabled.cast(sa.Integer)).label("disabled"),
            )
        ).one()

        critical_alerts = db.execute(
            select(func.count()).select_from(EarlyWarning)
            .where(EarlyWarning.severity.in_(["critical", "high"]),
                   EarlyWarning.status == "open",
                   EarlyWarning.is_deleted == False)
        ).scalar() or 0

        overdue_tasks = db.execute(
            select(func.count()).select_from(Task)
            .where(Task.status == "overdue", Task.is_deleted == False)
        ).scalar() or 0

        pending_refs = db.execute(
            select(func.count()).select_from(Referral)
            .where(Referral.status.in_(["pending", "in_progress"]))
        ).scalar() or 0

        visits_30d = db.execute(text("""
            SELECT COUNT(*) FROM home_visits
            WHERE visit_date::date >= CURRENT_DATE - INTERVAL '30 days'
        """)).scalar() or 0

        ref_completed = db.execute(
            select(func.count()).select_from(Referral)
            .where(Referral.status == "completed")
        ).scalar() or 0
        ref_total = db.execute(select(func.count()).select_from(Referral)).scalar() or 1

        high_risk = db.execute(
            select(func.count()).select_from(RiskScore)
            .where(RiskScore.risk_level.in_(["high", "critical"]),
                   RiskScore.is_deleted == False)
        ).scalar() or 0

        top_scorecards = db.execute(
            select(CommunityScorecard)
            .where(CommunityScorecard.is_deleted == False)
            .order_by(CommunityScorecard.overall_score.desc())
            .limit(5)
        ).scalars().all()

        district_visits = db.execute(text("""
            SELECT COALESCE(v.district,'Unknown') as district, COUNT(hv.id) as visits
            FROM volunteers v
            LEFT JOIN home_visits hv ON hv.volunteer_id = v.id
            GROUP BY v.district
            ORDER BY visits DESC LIMIT 10
        """)).fetchall()

        ref_by_status = db.execute(
            select(Referral.status, func.count()).group_by(Referral.status)
        ).all()

        monthly_trend = db.execute(text("""
            SELECT TO_CHAR(visit_date::date, 'YYYY-MM') as month, COUNT(*) as cnt
            FROM home_visits GROUP BY month ORDER BY month DESC LIMIT 6
        """)).fetchall()

    # ── Executive KPIs ────────────────────────────────────────────────────────
    st.subheader("Executive KPIs")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Citizens", total_citizens)
    c2.metric("Active Volunteers", active_vols)
    c3.metric("🚨 Critical Alerts", critical_alerts,
              delta=None if critical_alerts == 0 else f"{critical_alerts} open",
              delta_color="inverse")
    c4.metric("⚠️ Overdue Tasks", overdue_tasks,
              delta_color="inverse" if overdue_tasks else "off")
    c5.metric("Pending Referrals", pending_refs)
    c6.metric("Ref Completion", f"{round(ref_completed/max(ref_total,1)*100,1)}%")

    c7, c8, c9, c10 = st.columns(4)
    c7.metric("Visits (30d)", visits_30d)
    c8.metric("Elderly Population", int(cit_row.elderly or 0))
    c9.metric("High Priority Cases", high_risk)
    c10.metric("Vol Coverage", f"1:{round(total_citizens/max(active_vols,1),0):.0f}",
               help="Citizens per volunteer")

    st.divider()

    col1, col2 = st.columns(2)

    # District activity
    if district_visits:
        fig1 = px.bar(
            x=[r[0] for r in district_visits],
            y=[r[1] for r in district_visits],
            title="Home Visits by District",
            color_discrete_sequence=["#1e3a5f"],
        )
        col1.plotly_chart(fig1, use_container_width=True)

    # Referral aging
    ref_map = {r[0]: r[1] for r in ref_by_status}
    if ref_map:
        fig2 = px.pie(
            names=list(ref_map.keys()),
            values=list(ref_map.values()),
            title="Referral Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        col2.plotly_chart(fig2, use_container_width=True)

    # Monthly trend
    if monthly_trend:
        months = [r[0] for r in reversed(monthly_trend)]
        counts = [r[1] for r in reversed(monthly_trend)]
        fig3 = px.area(x=months, y=counts, title="Visit Activity Trend",
                       color_discrete_sequence=["#1e3a5f"])
        st.plotly_chart(fig3, use_container_width=True)

    # Community rankings
    if top_scorecards:
        st.subheader("🏆 Top Community Rankings")
        import pandas as pd
        df = pd.DataFrame([{
            "Rank": i + 1,
            "Community": sc.community_name,
            "District": sc.district or "",
            "Overall Score": f"{sc.overall_score}%",
            "Period": f"{sc.year}/{sc.month:02d}",
        } for i, sc in enumerate(top_scorecards)])
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Alert summary
    with get_sync_db() as db:
        recent_alerts = db.execute(
            select(EarlyWarning)
            .where(EarlyWarning.status == "open",
                   EarlyWarning.is_deleted == False)
            .order_by(EarlyWarning.created_at.desc())
            .limit(5)
        ).scalars().all()

    if recent_alerts:
        st.subheader("🚨 Recent Open Alerts")
        for alert in recent_alerts:
            icon = "🚨" if alert.severity == "critical" else "⚠️"
            st.warning(f"{icon} **{alert.title}** — {alert.alert_type} ({alert.severity})")
