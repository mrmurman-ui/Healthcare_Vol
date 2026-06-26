"""Analytics module — charts and insights."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en

import sqlalchemy as sa

import plotly.express as px
import streamlit as st
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
from app.modules.citizens.model import Citizen
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.modules.referrals.model import Referral
from app.modules.tasks.model import Task
from app.modules.volunteers.model import Volunteer


def render_analytics() -> None:
    st.header("📊 " + t("nav_analytics"))

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        _t("ผลการปฏิบัติงาน อสม.", "Volunteer Performance"),
        _t("แนวโน้มการเยี่ยมบ้าน", "Visit Trends"),
        _t("แนวโน้มการส่งต่อ", "Referral Trends"),
        _t("แนวโน้มงาน", "Task Trends"),
        _t("ประชากร", "Population"),
    ])

    with get_sync_db() as db:
        # Volunteer by status
        vol_rows = db.execute(
            select(Volunteer.status, func.count()).group_by(Volunteer.status)
        ).all()

        # Visits by month
        visit_rows = db.execute(text("""
            SELECT TO_CHAR(visit_date::date, 'YYYY-MM') as month, COUNT(*) as cnt
            FROM home_visits
            GROUP BY month ORDER BY month DESC LIMIT 12
        """)).fetchall()

        # Referrals by status
        ref_rows = db.execute(
            select(Referral.status, func.count()).group_by(Referral.status)
        ).all()

        # Tasks by priority
        task_rows = db.execute(
            select(Task.priority, func.count())
            .where(Task.is_deleted == False)
            .group_by(Task.priority)
        ).all()

        # Citizen flags
        cit_row = db.execute(
            select(
                func.count().label("total"),
                func.sum(Citizen.is_elderly.cast(sa.Integer)).label("elderly"),
                func.sum(Citizen.is_disabled.cast(sa.Integer)).label("disabled"),
                func.sum(Citizen.is_bedridden.cast(sa.Integer)).label("bedridden"),
                func.sum(Citizen.is_pregnant.cast(sa.Integer)).label("pregnant"),
            )
        ).one()

        # Referrals by target
        ref_target_rows = db.execute(
            select(Referral.target, func.count()).group_by(Referral.target)
        ).all()

    # ── Tab 1: Volunteer Performance ──────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns(2)
        if vol_rows:
            fig = px.pie(
                names=[r[0] for r in vol_rows],
                values=[r[1] for r in vol_rows],
                title=_t("อาสาสมัครตามสถานะ","Volunteers by Status"),
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            col1.plotly_chart(fig, use_container_width=True)

        # Visits per volunteer (top 10)
        with get_sync_db() as db2:
            top_vol = db2.execute(text("""
                SELECT v.full_name, COUNT(hv.id) as visits
                FROM volunteers v
                LEFT JOIN home_visits hv ON hv.volunteer_id = v.id
                GROUP BY v.id, v.full_name
                ORDER BY visits DESC LIMIT 10
            """)).fetchall()

        if top_vol:
            fig2 = px.bar(
                x=[r[0] for r in top_vol],
                y=[r[1] for r in top_vol],
                title=_t("อสม. 10 อันดับตามการเยี่ยมบ้าน","Top 10 Volunteers by Home Visits"),
                color_discrete_sequence=["#1e3a5f"],
            )
            col2.plotly_chart(fig2, use_container_width=True)

    # ── Tab 2: Visit Trends ───────────────────────────────────────────────────
    with tab2:
        if visit_rows:
            months = [r[0] for r in reversed(visit_rows)]
            counts = [r[1] for r in reversed(visit_rows)]
            fig = px.line(
                x=months, y=counts,
                title=_t("การเยี่ยมบ้านรายเดือน", "Home Visits per Month"),
                markers=True,
                color_discrete_sequence=["#1e3a5f"],
            )
            fig.update_layout(
                xaxis_title=_t("เดือน", "Month"),
                yaxis_title=_t("จำนวนการเยี่ยม", "Visits"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(_t("ยังไม่มีข้อมูลการเยี่ยมบ้าน", "No visit data yet."))

        # Visit type breakdown
        with get_sync_db() as db2:
            vtype_rows = db2.execute(
                select(HomeVisit.visit_type, func.count()).group_by(HomeVisit.visit_type)
            ).all()
        if vtype_rows:
            fig2 = px.pie(
                names=[r[0] for r in vtype_rows],
                values=[r[1] for r in vtype_rows],
                title=_t("การเยี่ยมบ้านตามประเภท", "Visits by Type"),
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 3: Referral Trends ────────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns(2)
        if ref_rows:
            fig = px.pie(
                names=[r[0] for r in ref_rows],
                values=[r[1] for r in ref_rows],
                title=_t("การส่งต่อตามสถานะ", "Referrals by Status"),
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            col1.plotly_chart(fig, use_container_width=True)

        if ref_target_rows:
            fig2 = px.bar(
                x=[r[0] for r in ref_target_rows],
                y=[r[1] for r in ref_target_rows],
                title=_t("การส่งต่อตามจุดหมาย", "Referrals by Target"),
                color_discrete_sequence=["#2e86ab"],
            )
            col2.plotly_chart(fig2, use_container_width=True)

    # ── Tab 4: Task Trends ────────────────────────────────────────────────────
    with tab4:
        col1, col2 = st.columns(2)
        if task_rows:
            priority_colors = {"critical": "red", "high": "orange",
                               "medium": "gold", "low": "green"}
            fig = px.bar(
                x=[r[0] for r in task_rows],
                y=[r[1] for r in task_rows],
                title=_t("งานตามระดับความสำคัญ", "Tasks by Priority"),
                color=[r[0] for r in task_rows],
                color_discrete_map=priority_colors,
            )
            col1.plotly_chart(fig, use_container_width=True)

        with get_sync_db() as db2:
            tstatus_rows = db2.execute(
                select(Task.status, func.count())
                .where(Task.is_deleted == False)
                .group_by(Task.status)
            ).all()
        if tstatus_rows:
            fig2 = px.pie(
                names=[r[0] for r in tstatus_rows],
                values=[r[1] for r in tstatus_rows],
                title=_t("งานตามสถานะ", "Tasks by Status"),
            )
            col2.plotly_chart(fig2, use_container_width=True)

    # ── Tab 5: Population ─────────────────────────────────────────────────────
    with tab5:
        total = int(cit_row.total or 0)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(_t("ประชาชนทั้งหมด", "Total Citizens"), total)
        c2.metric(_t("ผู้สูงอายุ", "Elderly"), int(cit_row.elderly or 0))
        c3.metric(_t("ผู้พิการ", "Disabled"), int(cit_row.disabled or 0))
        c4.metric(_t("ติดเตียง", "Bedridden"), int(cit_row.bedridden or 0))
        c5.metric(_t("ตั้งครรภ์", "Pregnant"), int(cit_row.pregnant or 0))

        if total:
            flag_data = {
                _t("ผู้สูงอายุ", "Elderly"): int(cit_row.elderly or 0),
                _t("ผู้พิการ", "Disabled"): int(cit_row.disabled or 0),
                _t("ติดเตียง", "Bedridden"): int(cit_row.bedridden or 0),
                _t("ตั้งครรภ์", "Pregnant"): int(cit_row.pregnant or 0),
            }
            fig = px.bar(
                x=list(flag_data.keys()),
                y=list(flag_data.values()),
                title=_t("การกระจายกลุ่มเปราะบาง", "Vulnerability Flags Distribution"),
                color_discrete_sequence=["#e63946"],
            )
            st.plotly_chart(fig, use_container_width=True)

        # Gender breakdown
        with get_sync_db() as db2:
            gender_rows = db2.execute(
                select(Citizen.gender, func.count()).group_by(Citizen.gender)
            ).all()
        if gender_rows:
            fig2 = px.pie(
                names=[r[0] or _t("ไม่ระบุ", "unknown") for r in gender_rows],
                values=[r[1] for r in gender_rows],
                title=_t("ประชาชนตามเพศ", "Citizens by Gender"),
            )
            st.plotly_chart(fig2, use_container_width=True)
