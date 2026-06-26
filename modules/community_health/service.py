"""Community Health Dashboard, Elderly Monitoring, Health Analytics."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang","TH") == "TH" else en


import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import func, select, text

from app.core.db_sync import get_sync_db
from app.modules.citizens.model import Citizen
from app.modules.early_warning.model import CVIScore, EarlyWarning
from app.modules.health_assessments.model import HealthAssessment
from app.modules.health_profiles.model import HealthProfile
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.modules.referrals.model import Referral
from app.modules.volunteers.model import Volunteer
import sqlalchemy as sa


# ── Community Health Dashboard ────────────────────────────────────────────────

def render_community_health() -> None:
    st.header("🏘️ " + t("nav_community_health"))

    with get_sync_db() as db:
        total_citizens = db.execute(select(func.count()).select_from(Citizen)).scalar() or 0
        total_volunteers = db.execute(select(func.count()).select_from(Volunteer)).scalar() or 0
        total_visits = db.execute(select(func.count()).select_from(HomeVisit)).scalar() or 0
        total_assessments = db.execute(
            select(func.count()).select_from(HealthAssessment)
            .where(HealthAssessment.is_deleted == False)
        ).scalar() or 0
        total_referrals = db.execute(select(func.count()).select_from(Referral)).scalar() or 0

        # Vulnerability counts
        cit_row = db.execute(
            select(
                func.sum(Citizen.is_elderly.cast(sa.Integer)).label("elderly"),
                func.sum(Citizen.is_disabled.cast(sa.Integer)).label("disabled"),
                func.sum(Citizen.is_bedridden.cast(sa.Integer)).label("bedridden"),
                func.sum(Citizen.is_living_alone.cast(sa.Integer)).label("alone"),
            )
        ).one()

        # Profile-based counts
        hp_row = db.execute(
            select(
                func.sum(HealthProfile.is_homebound.cast(sa.Integer)).label("homebound"),
                func.sum(HealthProfile.has_diabetes.cast(sa.Integer)).label("diabetes"),
                func.sum(HealthProfile.has_hypertension.cast(sa.Integer)).label("hypertension"),
                func.sum(HealthProfile.has_heart_disease.cast(sa.Integer)).label("heart"),
            )
        ).one()

        # CVI distribution
        cvi_dist = db.execute(
            select(CVIScore.category, func.count()).group_by(CVIScore.category)
        ).all()

        # Open warnings
        open_warnings = db.execute(
            select(func.count()).select_from(EarlyWarning)
            .where(EarlyWarning.status == "open", EarlyWarning.is_deleted == False)
        ).scalar() or 0

        # Referral status
        ref_status = db.execute(
            select(Referral.status, func.count()).group_by(Referral.status)
        ).all()

    st.subheader(_t("ภาพรวมประชากร", "Population Overview"))
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(_t("ประชาชนทั้งหมด", "Total Citizens"), total_citizens)
    c2.metric("👴 " + _t("ผู้สูงอายุ", "Elderly"), int(cit_row.elderly or 0))
    c3.metric("♿ " + _t("ผู้พิการ", "Disabled"), int(cit_row.disabled or 0))
    c4.metric("🛏️ " + _t("ติดเตียง", "Bedridden"), int(cit_row.bedridden or 0))
    c5.metric("🏠 " + _t("อยู่คนเดียว", "Living Alone"), int(cit_row.alone or 0))

    c6, c7, c8, c9, c10 = st.columns(5)
    c6.metric(_t("อาสาสมัคร", "Volunteers"), total_volunteers)
    c7.metric(_t("การเยี่ยมบ้านทั้งหมด", "Total Visits"), total_visits)
    c8.metric(_t("การประเมิน", "Assessments"), total_assessments)
    c9.metric("⚠️ " + _t("การแจ้งเตือนที่เปิดอยู่", "Open Alerts"), open_warnings)
    c10.metric(_t("การส่งต่อ", "Referrals"), total_referrals)

    st.divider()

    col1, col2 = st.columns(2)

    # CVI distribution
    cvi_map = {r[0]: r[1] for r in cvi_dist}
    if cvi_map:
        fig = px.pie(
            names=list(cvi_map.keys()),
            values=list(cvi_map.values()),
            title=_t("การกระจายความเปราะบางของชุมชน", "Community Vulnerability Distribution"),
            color_discrete_map={
                "critical": "#e63946", "high": "#f4a261",
                "moderate": "#e9c46a", "low": "#2a9d8f",
            },
        )
        col1.plotly_chart(fig, use_container_width=True)

    # Chronic conditions
    chronic = {
        _t("เบาหวาน", "Diabetes"): int(hp_row.diabetes or 0),
        _t("ความดันโลหิตสูง", "Hypertension"): int(hp_row.hypertension or 0),
        _t("โรคหัวใจ", "Heart Disease"): int(hp_row.heart or 0),
    }
    fig2 = px.bar(
        x=list(chronic.keys()), y=list(chronic.values()),
        title=_t("จำนวนโรคเรื้อรัง (รายงานตนเอง)", "Chronic Condition Counts (self-reported)"),
        color_discrete_sequence=["#1e3a5f"],
    )
    col2.plotly_chart(fig2, use_container_width=True)

    # Referral status
    ref_map = {r[0]: r[1] for r in ref_status}
    if ref_map:
        fig3 = px.bar(
            x=list(ref_map.keys()), y=list(ref_map.values()),
            title=_t("การกระจายสถานะการส่งต่อ", "Referral Status Distribution"),
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig3, use_container_width=True)


# ── Elderly Monitoring ────────────────────────────────────────────────────────

def render_elderly_monitoring() -> None:
    st.header("👴 " + t("nav_elderly_monitoring"))

    with get_sync_db() as db:
        # Elderly citizens with their profiles
        elderly = db.execute(
            select(Citizen, HealthProfile)
            .outerjoin(HealthProfile, HealthProfile.citizen_id == Citizen.id)
            .where(Citizen.is_elderly == True)
            .order_by(Citizen.full_name)
            .limit(200)
        ).all()

        total = len(elderly)
        living_alone = sum(1 for _, hp in elderly if hp and hp.lives_alone_profile)
        homebound = sum(1 for _, hp in elderly if hp and hp.is_homebound)
        no_caregiver = sum(1 for _, hp in elderly if hp and not hp.has_caregiver)
        high_cvi = db.execute(
            select(func.count()).select_from(CVIScore)
            .join(Citizen, CVIScore.citizen_id == Citizen.id)
            .where(Citizen.is_elderly == True, CVIScore.category.in_(["high", "critical"]))
        ).scalar() or 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(_t("ผู้สูงอายุทั้งหมด","Total Elderly"), total)
    c2.metric(_t("อยู่คนเดียว","Living Alone"), living_alone)
    c3.metric(_t("ติดบ้าน","Homebound"), homebound)
    c4.metric(_t("ไม่มีผู้ดูแล","No Caregiver"), no_caregiver)
    c5.metric(_t("CVI สูง/วิกฤต","High/Critical CVI"), high_cvi)

    st.divider()
    st.subheader(_t("รายชื่อผู้สูงอายุ","Elderly Citizens List"))

    import pandas as pd
    if elderly:
        df = pd.DataFrame([{
            _t("ชื่อ","Name"): c.full_name,
            _t("เบอร์โทร","Phone"): c.phone or "",
            _t("อยู่คนเดียว","Living Alone"): "✓" if hp and hp.lives_alone_profile else "",
            _t("ติดบ้าน","Homebound"): "✓" if hp and hp.is_homebound else "",
            "Has Caregiver": "✓" if hp and hp.has_caregiver else "✗",
            "Chronic Conditions": sum([
                hp.has_diabetes, hp.has_hypertension, hp.has_heart_disease
            ]) if hp else 0,
            _t("ต้องเยี่ยมบ้าน","Needs Visit"): "✓" if hp and hp.needs_home_visit else "",
        } for c, hp in elderly])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No elderly citizens registered.")


# ── Health Analytics ──────────────────────────────────────────────────────────

def render_health_analytics() -> None:
    st.header("📊 " + t("nav_health_analytics"))

    with get_sync_db() as db:
        # BMI distribution
        bmi_rows = db.execute(
            select(HealthAssessment.bmi)
            .where(HealthAssessment.bmi.isnot(None), HealthAssessment.is_deleted == False)
            .limit(5000)
        ).scalars().all()

        # BP distribution
        bp_rows = db.execute(
            select(HealthAssessment.bp_systolic)
            .where(HealthAssessment.bp_systolic.isnot(None), HealthAssessment.is_deleted == False)
            .limit(5000)
        ).scalars().all()

        # Assessment trend by month
        assessment_trend = db.execute(text("""
            SELECT TO_CHAR(assessment_date::date, 'YYYY-MM') as month, COUNT(*) as cnt
            FROM health_assessments
            WHERE is_deleted = false
            GROUP BY month ORDER BY month DESC LIMIT 12
        """)).fetchall()

        # Age pyramid
        age_rows = db.execute(text("""
            SELECT
                CASE
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 10 THEN '0-9'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 20 THEN '10-19'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 30 THEN '20-29'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 40 THEN '30-39'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 50 THEN '40-49'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 60 THEN '50-59'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 70 THEN '60-69'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 80 THEN '70-79'
                    ELSE '80+'
                END as age_group,
                COUNT(*) as cnt
            FROM citizens
            WHERE date_of_birth IS NOT NULL
            GROUP BY age_group ORDER BY age_group
        """)).fetchall()

    tab1, tab2, tab3, tab4 = st.tabs([
        _t("พีระมิดอายุ","Age Pyramid"), _t("การกระจาย BMI","BMI Distribution"), _t("ความดันโลหิต","Blood Pressure"), _t("แนวโน้มการประเมิน","Assessment Trends")
    ])

    with tab1:
        if age_rows:
            fig = px.bar(
                x=[r[0] for r in age_rows],
                y=[r[1] for r in age_rows],
                title="Population Age Distribution",
                color_discrete_sequence=["#1e3a5f"],
                labels={"x": "Age Group", "y": "Count"},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No birth date data available.")

    with tab2:
        if bmi_rows:
            fig = px.histogram(
                x=list(bmi_rows), nbins=30,
                title=_t("การกระจาย BMI","BMI Distribution"),
                color_discrete_sequence=["#2a9d8f"],
                labels={"x": "BMI"},
            )
            fig.add_vline(x=18.5, line_dash="dash", line_color="blue",
                         annotation_text="Underweight")
            fig.add_vline(x=23, line_dash="dash", line_color="green",
                         annotation_text="Normal")
            fig.add_vline(x=25, line_dash="dash", line_color="orange",
                         annotation_text="Overweight")
            st.plotly_chart(fig, use_container_width=True)
            st.metric("Average BMI", round(sum(bmi_rows) / len(bmi_rows), 1))
        else:
            st.info("No BMI data yet.")

    with tab3:
        if bp_rows:
            fig = px.histogram(
                x=list(bp_rows), nbins=30,
                title="Systolic Blood Pressure Distribution",
                color_discrete_sequence=["#e63946"],
                labels={"x": "Systolic BP (mmHg)"},
            )
            fig.add_vline(x=140, line_dash="dash", line_color="red",
                         annotation_text="Elevated (140)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No blood pressure data yet.")

    with tab4:
        if assessment_trend:
            months = [r[0] for r in reversed(assessment_trend)]
            counts = [r[1] for r in reversed(assessment_trend)]
            fig = px.line(
                x=months, y=counts,
                title="Health Assessments per Month",
                markers=True,
                color_discrete_sequence=["#1e3a5f"],
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No assessment trend data yet.")
