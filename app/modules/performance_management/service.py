"""Performance Management — KPI tracking and trend analysis."""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import Float, String, Text, func, select, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.shared.base_model import UUIDBase


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


METRIC_CATEGORIES = [
    "volunteer_productivity", "case_closure", "referral_completion",
    "assessment_coverage", "home_visit_frequency", "campaign_coverage",
    "social_support", "care_plan",
]
METRIC_STATUSES = ["on_track", "at_risk", "off_track", "achieved"]

METRIC_CATEGORIES_TH = {
    "volunteer_productivity": "ประสิทธิภาพอาสาสมัคร",
    "case_closure": "การปิดกรณี",
    "referral_completion": "การส่งต่อสำเร็จ",
    "assessment_coverage": "การครอบคลุมการประเมิน",
    "home_visit_frequency": "ความถี่การเยี่ยมบ้าน",
    "campaign_coverage": "การครอบคลุมแคมเปญ",
    "social_support": "การสนับสนุนทางสังคม",
    "care_plan": "แผนการดูแล",
}
METRIC_STATUSES_TH = {
    "on_track": "เป็นไปตามแผน",
    "at_risk": "มีความเสี่ยง",
    "off_track": "ไม่เป็นไปตามแผน",
    "achieved": "บรรลุเป้าหมาย",
}
STATUS_COLORS = {
    "achieved": "🟢",
    "on_track": "🔵",
    "at_risk": "🟡",
    "off_track": "🔴",
}


# ── Model ─────────────────────────────────────────────────────────────────────

class PerformanceMetric(UUIDBase):
    __tablename__ = "performance_metrics"

    metric_name: Mapped[str] = mapped_column(String(300), nullable=False)
    metric_category: Mapped[str] = mapped_column(String(100), default="volunteer_productivity")
    target: Mapped[float | None] = mapped_column(Float)
    current_value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="on_track")
    period: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False)


def compute_status(current: float, target: float) -> str:
    if current >= target:
        return "achieved"
    ratio = current / max(target, 0.001)
    if ratio >= 0.9:
        return "on_track"
    if ratio >= 0.7:
        return "at_risk"
    return "off_track"


def render_performance_management() -> None:
    st.header("📈 " + t("nav_performance"))

    with get_sync_db() as db:
        metrics = db.execute(
            select(PerformanceMetric)
            .where(PerformanceMetric.is_deleted == False)
            .order_by(PerformanceMetric.metric_category, PerformanceMetric.metric_name)
        ).scalars().all()

    # Live KPIs from DB
    with get_sync_db() as db:
        vol_count = db.execute(select(func.count()).select_from(
            __import__("app.modules.volunteers.model", fromlist=["Volunteer"]).Volunteer
        )).scalar() or 0
        visit_30d = db.execute(text("""
            SELECT COUNT(*) FROM home_visits
            WHERE visit_date::date >= CURRENT_DATE - INTERVAL '30 days'
        """)).scalar() or 0
        ref_completed = db.execute(text("""
            SELECT COUNT(*) FROM referrals WHERE status = 'completed'
        """)).scalar() or 0
        ref_total = db.execute(text("SELECT COUNT(*) FROM referrals")).scalar() or 1
        assess_30d = db.execute(text("""
            SELECT COUNT(*) FROM health_assessments
            WHERE assessment_date::date >= CURRENT_DATE - INTERVAL '30 days'
            AND is_deleted = false
        """)).scalar() or 0

    ref_rate = round((ref_completed / max(ref_total, 1)) * 100, 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(_t("อาสาสมัครที่ใช้งาน", "Active Volunteers"), vol_count)
    c2.metric(_t("การเยี่ยม (30 วัน)", "Visits (30d)"), visit_30d)
    c3.metric(_t("การส่งต่อสำเร็จ", "Referral Completion"), f"{ref_rate}%")
    c4.metric(_t("การประเมิน (30 วัน)", "Assessments (30d)"), assess_30d)

    st.divider()

    is_thai = _t("th", "en") == "th"

    # Recorded metrics
    if metrics:
        df = pd.DataFrame([{
            _t("สถานะ", "Status"): STATUS_COLORS.get(m.status, "") + " " + (METRIC_STATUSES_TH.get(m.status, m.status) if is_thai else m.status),
            _t("ตัวชี้วัด", "Metric"): m.metric_name,
            _t("หมวดหมู่", "Category"): METRIC_CATEGORIES_TH.get(m.metric_category, m.metric_category) if is_thai else m.metric_category,
            _t("เป้าหมาย", "Target"): f"{m.target}{m.unit or ''}",
            _t("ค่าปัจจุบัน", "Current"): f"{m.current_value}{m.unit or ''}",
            _t("ช่วงเวลา", "Period"): m.period or "",
        } for m in metrics])

        # Summary by status
        from collections import Counter
        status_counts = Counter(m.status for m in metrics)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🟢 " + _t("บรรลุเป้าหมาย", "Achieved"), status_counts.get("achieved", 0))
        col2.metric("🔵 " + _t("เป็นไปตามแผน", "On Track"), status_counts.get("on_track", 0))
        col3.metric("🟡 " + _t("มีความเสี่ยง", "At Risk"), status_counts.get("at_risk", 0))
        col4.metric("🔴 " + _t("ไม่เป็นไปตามแผน", "Off Track"), status_counts.get("off_track", 0))

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Chart
        if len(metrics) > 1:
            chart_data = [m for m in metrics if m.current_value is not None and m.target]
            if chart_data:
                fig = px.bar(
                    x=[m.metric_name for m in chart_data],
                    y=[m.current_value for m in chart_data],
                    title=_t("ผลลัพธ์ KPI เทียบกับเป้าหมาย", "KPI Achievement vs Target"),
                    color=[m.status for m in chart_data],
                    color_discrete_map={
                        "achieved": "#2a9d8f", "on_track": "#457b9d",
                        "at_risk": "#e9c46a", "off_track": "#e63946",
                    },
                )
                for m in chart_data:
                    if m.target:
                        fig.add_hline(y=m.target, line_dash="dot", line_color="gray",
                                     annotation_text=f"T:{m.target}")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(_t("ยังไม่มีตัวชี้วัดที่บันทึก", "No metrics recorded yet."))

    st.divider()
    with st.expander("➕ " + _t("เพิ่มตัวชี้วัด", "Add Metric")):
        with st.form("add_metric"):
            col1, col2 = st.columns(2)
            name = col1.text_input(_t("ชื่อตัวชี้วัด", "Metric Name"))
            cat_options = [METRIC_CATEGORIES_TH.get(c, c) for c in METRIC_CATEGORIES] if is_thai else METRIC_CATEGORIES
            cat_display = col2.selectbox(_t("หมวดหมู่", "Category"), cat_options)
            cat = METRIC_CATEGORIES[[METRIC_CATEGORIES_TH.get(c, c) for c in METRIC_CATEGORIES].index(cat_display)] if is_thai else cat_display
            col3, col4, col5 = st.columns(3)
            target = col3.number_input(_t("เป้าหมาย", "Target"), min_value=0.0, value=0.0)
            current = col4.number_input(_t("ค่าปัจจุบัน", "Current Value"), min_value=0.0, value=0.0)
            unit = col5.text_input(_t("หน่วย (เช่น %)", "Unit (e.g. %)"))
            period = st.text_input(_t("ช่วงเวลา (เช่น 2026-Q1)", "Period (e.g. 2026-Q1)"))
            notes = st.text_area(_t("หมายเหตุ", "Notes"))
            submitted = st.form_submit_button(t("save"))

        if submitted and name:
            status = compute_status(current, target) if target else "on_track"
            user = get_current_user()
            with get_sync_db() as db:
                db.add(PerformanceMetric(
                    metric_name=name, metric_category=cat,
                    target=target or None, current_value=current,
                    unit=unit or None, status=status,
                    period=period or None, notes=notes or None,
                    created_by=user.email if user else "system",
                    updated_by=user.email if user else "system",
                ))
            st.success(_t("บันทึกตัวชี้วัดสำเร็จ", "Metric saved."))
            st.rerun()
