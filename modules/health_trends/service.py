"""Health Trends — longitudinal tracking per citizen."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en


import uuid

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import select

from app.core.db_sync import get_sync_db
from app.modules.citizens.model import Citizen
from app.modules.health_assessments.model import HealthAssessment
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.shared.date_utils import fmt_date
from app.modules.referrals.model import Referral


def render_health_trends() -> None:
    st.header("📈 " + t("nav_health_trends"))

    search = st.text_input(_t("ค้นหาชื่อประชาชน","Search Citizen Name"), key="ht_search")
    with get_sync_db() as db:
        stmt = select(Citizen)
        if search:
            stmt = stmt.where(Citizen.full_name.ilike(f"%{search}%"))
        citizens = db.execute(stmt.limit(50)).scalars().all()

    if not citizens:
        st.info("Search for a citizen above.")
        return

    options = {f"{c.full_name} (ID: {str(c.id)[:8]})": c.id for c in citizens}
    selected = st.selectbox(_t("เลือกประชาชน","Select Citizen"), list(options.keys()))
    citizen_id = options[selected]

    with get_sync_db() as db:
        citizen = db.get(Citizen, citizen_id)
        assessments = list(db.execute(
            select(HealthAssessment)
            .where(HealthAssessment.citizen_id == citizen_id,
                   HealthAssessment.is_deleted == False)
            .order_by(HealthAssessment.assessment_date.asc())
        ).scalars().all())

        visits = list(db.execute(
            select(HomeVisit)
            .where(HomeVisit.citizen_id == citizen_id)
            .order_by(HomeVisit.visit_date.desc())
            .limit(20)
        ).scalars().all())

        referrals = list(db.execute(
            select(Referral)
            .where(Referral.citizen_id == citizen_id)
            .order_by(Referral.referral_date.desc())
            .limit(10)
        ).scalars().all())

    # ── Profile Summary ───────────────────────────────────────────────────────
    st.subheader(f"👤 {citizen.full_name}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(_t("การประเมินทั้งหมด","Total Assessments"), len(assessments))
    col2.metric(_t("การเยี่ยมบ้านทั้งหมด","Total Visits"), len(visits))
    col3.metric(_t("การส่งต่อทั้งหมด","Total Referrals"), len(referrals))

    if assessments:
        latest = assessments[-1]
        col4.metric("Latest BMI", latest.bmi or "—")

    st.divider()

    if not assessments:
        st.info(_t("ยังไม่มีข้อมูลการประเมินสำหรับกราฟแนวโน้ม","No assessment data yet for trend charts."))
        return

    dates = [a.assessment_date for a in assessments]

    tab1, tab2, tab3, tab4 = st.tabs(["Weight & BMI", "Blood Pressure", "Pulse & Temp", "Activity"])

    # ── Weight & BMI ──────────────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns(2)
        weights = [a.weight_kg for a in assessments if a.weight_kg]
        w_dates = [a.assessment_date for a in assessments if a.weight_kg]
        if weights:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=w_dates, y=weights, mode="lines+markers",
                                     name="Weight (kg)", line=dict(color="#1e3a5f")))
            fig.update_layout(title="Weight Trend (kg)", xaxis_title=_t("วันที่","Date"),
                              yaxis_title="Weight (kg)")
            col1.plotly_chart(fig, use_container_width=True)

        bmis = [a.bmi for a in assessments if a.bmi]
        b_dates = [a.assessment_date for a in assessments if a.bmi]
        if bmis:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=b_dates, y=bmis, mode="lines+markers",
                                       name="BMI", line=dict(color="#e63946")))
            fig2.add_hline(y=23, line_dash="dash", line_color="green",
                           annotation_text="Normal limit (23)")
            fig2.add_hline(y=25, line_dash="dash", line_color="orange",
                           annotation_text="Overweight (25)")
            fig2.update_layout(title=_t("แนวโน้ม BMI","BMI Trend"), xaxis_title=_t("วันที่","Date"), yaxis_title="BMI")
            col2.plotly_chart(fig2, use_container_width=True)

    # ── Blood Pressure ────────────────────────────────────────────────────────
    with tab2:
        sys_vals = [a.bp_systolic for a in assessments if a.bp_systolic]
        dia_vals = [a.bp_diastolic for a in assessments if a.bp_diastolic]
        bp_dates = [a.assessment_date for a in assessments if a.bp_systolic]

        if sys_vals:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=bp_dates, y=sys_vals, mode="lines+markers",
                                     name=_t("ตัวบน","Systolic"), line=dict(color="#e63946")))
            fig.add_trace(go.Scatter(x=bp_dates, y=dia_vals, mode="lines+markers",
                                     name=_t("ตัวล่าง","Diastolic"), line=dict(color="#457b9d")))
            fig.add_hline(y=140, line_dash="dash", line_color="red",
                          annotation_text="High Systolic (140)")
            fig.add_hline(y=90, line_dash="dash", line_color="orange",
                          annotation_text="High Diastolic (90)")
            fig.update_layout(title=_t("แนวโน้มความดันโลหิต","Blood Pressure Trend"), xaxis_title=_t("วันที่","Date"),
                              yaxis_title="mmHg")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No blood pressure data.")

    # ── Pulse & Temp ─────────────────────────────────────────────────────────
    with tab3:
        col1, col2 = st.columns(2)
        pulses = [a.pulse_rate for a in assessments if a.pulse_rate]
        p_dates = [a.assessment_date for a in assessments if a.pulse_rate]
        if pulses:
            fig = px.line(x=p_dates, y=pulses, title=_t("แนวโน้มชีพจร","Pulse Rate Trend"),
                          markers=True, color_discrete_sequence=["#2a9d8f"])
            col1.plotly_chart(fig, use_container_width=True)

        temps = [a.temperature_c for a in assessments if a.temperature_c]
        t_dates = [a.assessment_date for a in assessments if a.temperature_c]
        if temps:
            fig2 = px.line(x=t_dates, y=temps, title="Temperature Trend (°C)",
                           markers=True, color_discrete_sequence=["#e9c46a"])
            col2.plotly_chart(fig2, use_container_width=True)

    # ── Activity ──────────────────────────────────────────────────────────────
    with tab4:
        col1, col2 = st.columns(2)
        if visits:
            import pandas as pd
            visit_df = pd.DataFrame([{_t("วันที่","Date"): fmt_date(v.visit_date), "Type": v.visit_type}
                                      for v in visits])
            col1.subheader("Recent Visits")
            col1.dataframe(visit_df, use_container_width=True, hide_index=True)

        if referrals:
            import pandas as pd
            ref_df = pd.DataFrame([{
                _t("วันที่","Date"): str(r.referral_date),
                "Target": r.target,
                "Status": r.status,
            } for r in referrals])
            col2.subheader("Referral History")
            col2.dataframe(ref_df, use_container_width=True, hide_index=True)
