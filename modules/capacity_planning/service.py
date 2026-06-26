"""Capacity Planning — volunteer workload, coverage gaps, resource distribution."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import Float, Integer, String, func, select, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.home_visits.model import HomeVisit
from app.modules.localization.service import t
from app.modules.volunteers.model import Volunteer
from app.shared.base_model import UUIDBase
import sqlalchemy as sa


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


# ── Model ─────────────────────────────────────────────────────────────────────

class CapacityPlan(UUIDBase):
    __tablename__ = "capacity_planning"

    district: Mapped[str | None] = mapped_column(String(100), index=True)
    community: Mapped[str | None] = mapped_column(String(100))
    population: Mapped[int | None] = mapped_column(Integer)
    elderly_population: Mapped[int | None] = mapped_column(Integer)
    volunteers: Mapped[int | None] = mapped_column(Integer)
    active_cases: Mapped[int | None] = mapped_column(Integer)
    workload_score: Mapped[float | None] = mapped_column(Float)
    snapshot_date: Mapped[str | None] = mapped_column(String(20))
    is_deleted: Mapped[bool] = mapped_column(default=False)


# ── Compute live capacity ─────────────────────────────────────────────────────

def compute_capacity(db) -> list[dict]:
    """Build capacity stats from existing data, grouped by district."""
    rows = db.execute(text("""
        SELECT
            COALESCE(v.district, 'Unknown') as district,
            COUNT(DISTINCT v.id) as volunteers,
            COUNT(DISTINCT c.id) as citizens,
            SUM(CASE WHEN c.is_elderly THEN 1 ELSE 0 END) as elderly,
            COUNT(DISTINCT hv.id) as visits_30d
        FROM volunteers v
        LEFT JOIN home_visits hv ON hv.volunteer_id = v.id
            AND hv.visit_date::date >= CURRENT_DATE - INTERVAL '30 days'
        CROSS JOIN (SELECT id, is_elderly FROM citizens LIMIT 1000) c
        GROUP BY v.district
        ORDER BY volunteers DESC
        LIMIT 50
    """)).fetchall()

    result = []
    for row in rows:
        vols = row[1] or 1
        citizens = row[2] or 0
        elderly = row[3] or 0
        visits = row[4] or 0
        pop_per_vol = round(citizens / vols, 1)
        workload = round((citizens / max(vols, 1)) * 0.4 + (elderly / max(vols, 1)) * 0.6, 1)
        result.append({
            _t("เขต", "District"): row[0],
            _t("อาสาสมัคร", "Volunteers"): vols,
            _t("ประชาชน", "Citizens"): citizens,
            _t("ผู้สูงอายุ", "Elderly"): elderly,
            _t("การเยี่ยม (30 วัน)", "Visits (30d)"): visits,
            _t("ประชาชน/อาสาสมัคร", "Citizens/Volunteer"): pop_per_vol,
            _t("คะแนนภาระงาน", "Workload Score"): workload,
        })
    return result


# ── Page ─────────────────────────────────────────────────────────────────────

def render_capacity_planning() -> None:
    st.header("📐 " + t("nav_capacity_planning"))

    with get_sync_db() as db:
        total_vols = db.execute(select(func.count()).select_from(Volunteer)).scalar() or 0
        total_cits = db.execute(select(func.count()).select_from(Citizen)).scalar() or 0
        elderly = db.execute(
            select(func.count()).select_from(Citizen).where(Citizen.is_elderly == True)
        ).scalar() or 0
        visits_30d = db.execute(text("""
            SELECT COUNT(*) FROM home_visits
            WHERE visit_date::date >= CURRENT_DATE - INTERVAL '30 days'
        """)).scalar() or 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(_t("อาสาสมัครทั้งหมด", "Total Volunteers"), total_vols)
    c2.metric(_t("ประชาชนทั้งหมด", "Total Citizens"), total_cits)
    c3.metric(_t("ผู้สูงอายุ", "Elderly"), elderly)
    c4.metric(_t("เฉลี่ยประชาชน/อาสาสมัคร", "Avg Citizens/Vol"), round(total_cits / max(total_vols, 1), 1))
    c5.metric(_t("การเยี่ยม (30 วัน)", "Visits (30d)"), visits_30d)

    st.divider()
    st.subheader(_t("การวิเคราะห์กำลังคนรายเขต", "District Capacity Analysis"))

    with get_sync_db() as db:
        capacity_data = compute_capacity(db)

    if capacity_data:
        df = pd.DataFrame(capacity_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        district_col = _t("เขต", "District")
        vol_col = _t("อาสาสมัคร", "Volunteers")
        workload_col = _t("คะแนนภาระงาน", "Workload Score")
        fig1 = px.bar(
            df, x=district_col, y=vol_col,
            title=_t("อาสาสมัครตามเขต", "Volunteers by District"),
            color_discrete_sequence=["#1e3a5f"],
        )
        col1.plotly_chart(fig1, use_container_width=True)

        fig2 = px.bar(
            df, x=district_col, y=workload_col,
            title=_t("คะแนนภาระงานตามเขต", "Workload Score by District"),
            color=workload_col,
            color_continuous_scale=["green", "yellow", "red"],
        )
        col2.plotly_chart(fig2, use_container_width=True)

        # Coverage gaps — districts with high workload
        gaps = df[df[workload_col] > df[workload_col].median()]
        if not gaps.empty:
            st.subheader("⚠️ " + _t("จุดอ่อนด้านการครอบคลุม (ภาระงานสูงกว่ามัธยฐาน)", "Coverage Gaps (Above Median Workload)"))
            st.dataframe(gaps, use_container_width=True, hide_index=True)
    else:
        st.info(_t("ข้อมูลไม่เพียงพอ กรุณาเพิ่มอาสาสมัครและประชาชนเพื่อดูการวิเคราะห์กำลังคน", "Insufficient data. Add volunteers and citizens to see capacity analysis."))

    st.divider()
    with st.expander("📥 " + _t("บันทึกภาพรวมกำลังคน", "Save Capacity Snapshot")):
        with st.form("cap_snapshot"):
            district = st.text_input(_t("เขต", "District"))
            community = st.text_input(_t("ชุมชน", "Community"))
            population = st.number_input(_t("ประชากร", "Population"), min_value=0, value=0)
            elderly_pop = st.number_input(_t("ประชากรผู้สูงอายุ", "Elderly Population"), min_value=0, value=0)
            vols = st.number_input(_t("อาสาสมัคร", "Volunteers"), min_value=0, value=0)
            cases = st.number_input(_t("เคสที่ใช้งาน", "Active Cases"), min_value=0, value=0)
            submitted = st.form_submit_button(t("save"))
        if submitted and district:
            from datetime import date
            user = get_current_user()
            workload = round((population / max(vols, 1)) * 0.4 + (elderly_pop / max(vols, 1)) * 0.6, 1)
            with get_sync_db() as db:
                db.add(CapacityPlan(
                    district=district, community=community,
                    population=population, elderly_population=elderly_pop,
                    volunteers=vols, active_cases=cases,
                    workload_score=workload,
                    snapshot_date=str(date.today()),
                    created_by=user.email if user else "system",
                    updated_by=user.email if user else "system",
                ))
            st.success("Snapshot saved.")
            st.rerun()
