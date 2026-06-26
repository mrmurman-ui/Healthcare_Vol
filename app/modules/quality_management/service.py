"""Quality Management — indicators, monthly tracking, trend charts."""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import Boolean, Float, Integer, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.shared.date_utils import fmt_date, ad_to_be_year, be_to_ad_year, is_thai
from app.shared.base_model import UUIDBase


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en

INDICATOR_CATEGORIES = [
    "coverage", "assessment", "follow_up", "referral",
    "social_support", "home_visit", "volunteer_activity",
]
PERIODS = ["monthly", "quarterly", "yearly"]

# Thai display labels for categories and periods
CATEGORY_LABELS_TH = {
    "coverage": "การครอบคลุม",
    "assessment": "การประเมิน",
    "follow_up": "การติดตาม",
    "referral": "การส่งต่อ",
    "social_support": "การสนับสนุนทางสังคม",
    "home_visit": "การเยี่ยมบ้าน",
    "volunteer_activity": "กิจกรรมอาสาสมัคร",
}
PERIOD_LABELS_TH = {
    "monthly": "รายเดือน",
    "quarterly": "รายไตรมาส",
    "yearly": "รายปี",
}


# ── Models ────────────────────────────────────────────────────────────────────

class QualityIndicator(UUIDBase):
    __tablename__ = "quality_indicators"

    indicator_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    indicator_name: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="coverage")
    description: Mapped[str | None] = mapped_column(Text)
    target_value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(50))
    period: Mapped[str] = mapped_column(String(20), default="monthly")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class QualityRecord(UUIDBase):
    __tablename__ = "quality_records"

    indicator_id: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int | None] = mapped_column(Integer)
    period_quarter: Mapped[int | None] = mapped_column(Integer)
    actual_value: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


# ── Seed default indicators ───────────────────────────────────────────────────

DEFAULT_INDICATORS = [
    ("QI001", "Home Visit Coverage Rate", "home_visit", 80.0, "%"),
    ("QI002", "Health Assessment Coverage Rate", "assessment", 70.0, "%"),
    ("QI003", "Elderly Assessment Rate", "assessment", 90.0, "%"),
    ("QI004", "Referral Completion Rate", "referral", 85.0, "%"),
    ("QI005", "Follow-Up Completion Rate", "follow_up", 80.0, "%"),
    ("QI006", "Volunteer Activity Rate", "volunteer_activity", 75.0, "%"),
    ("QI007", "Social Support Coverage", "social_support", 60.0, "%"),
    ("QI008", "High-Risk Citizen Coverage", "coverage", 95.0, "%"),
]

# Thai display names for indicator codes (DB stores English; Thai shown in UI only)
INDICATOR_NAMES_TH = {
    "QI001": "อัตราการครอบคลุมการเยี่ยมบ้าน",
    "QI002": "อัตราการครอบคลุมการประเมินสุขภาพ",
    "QI003": "อัตราการประเมินผู้สูงอายุ",
    "QI004": "อัตราการส่งต่อสำเร็จ",
    "QI005": "อัตราการติดตามสำเร็จ",
    "QI006": "อัตรากิจกรรมอาสาสมัคร",
    "QI007": "การครอบคลุมการสนับสนุนทางสังคม",
    "QI008": "การครอบคลุมประชาชนกลุ่มเสี่ยงสูง",
}


def seed_default_indicators(db) -> None:
    for code, name, cat, target, unit in DEFAULT_INDICATORS:
        existing = db.execute(
            select(QualityIndicator).where(QualityIndicator.indicator_code == code)
        ).scalar_one_or_none()
        if not existing:
            db.add(QualityIndicator(
                indicator_code=code, indicator_name=name,
                category=cat, target_value=target, unit=unit,
                created_by="system", updated_by="system",
            ))
    db.commit()


# ── Page ─────────────────────────────────────────────────────────────────────

def render_quality_management() -> None:
    st.header("✅ " + t("nav_quality_management"))

    tab1, tab2, tab3 = st.tabs([
        _t("ตัวชี้วัด", "Indicators"),
        _t("บันทึกข้อมูล", "Record Entry"),
        _t("แผนภูมิแนวโน้ม", "Trend Charts"),
    ])

    with get_sync_db() as db:
        seed_default_indicators(db)
        indicators = db.execute(
            select(QualityIndicator).where(
                QualityIndicator.active == True,
                QualityIndicator.is_deleted == False,
            )
        ).scalars().all()
        records = db.execute(
            select(QualityRecord)
            .where(QualityRecord.is_deleted == False)
            .order_by(QualityRecord.period_year.desc(), QualityRecord.period_month.desc())
            .limit(200)
        ).scalars().all()

    # ── Tab 1: Indicators ─────────────────────────────────────────────────────
    with tab1:
        if indicators:
            df = pd.DataFrame([{
                _t("รหัส", "Code"): ind.indicator_code,
                _t("ตัวชี้วัด", "Indicator"): INDICATOR_NAMES_TH.get(ind.indicator_code, ind.indicator_name) if _t("th", "en") == "th" else ind.indicator_name,
                _t("หมวดหมู่", "Category"): CATEGORY_LABELS_TH.get(ind.category, ind.category) if _t("th", "en") == "th" else ind.category,
                _t("เป้าหมาย", "Target"): f"{ind.target_value}{ind.unit or ''}",
                _t("ช่วงเวลา", "Period"): PERIOD_LABELS_TH.get(ind.period, ind.period) if _t("th", "en") == "th" else ind.period,
            } for ind in indicators])
            st.dataframe(df, use_container_width=True, hide_index=True)

        with st.expander("➕ " + _t("เพิ่มตัวชี้วัด", "Add Indicator")):
            with st.form("add_indicator"):
                col1, col2 = st.columns(2)
                code = col1.text_input(_t("รหัส (เช่น QI009)", "Code (e.g. QI009)"))
                name = col2.text_input(_t("ชื่อตัวชี้วัด", "Indicator Name"))
                # Show Thai labels in dropdown but store English values
                is_thai_mode = _t("th", "en") == "th"
                cat_options = [CATEGORY_LABELS_TH.get(c, c) for c in INDICATOR_CATEGORIES] if is_thai_mode else INDICATOR_CATEGORIES
                cat_display = col1.selectbox(_t("หมวดหมู่", "Category"), cat_options)
                cat = INDICATOR_CATEGORIES[[CATEGORY_LABELS_TH.get(c, c) for c in INDICATOR_CATEGORIES].index(cat_display)] if is_thai_mode else cat_display
                target = col2.number_input(_t("ค่าเป้าหมาย", "Target Value"), min_value=0.0, value=80.0)
                unit = col1.text_input(_t("หน่วย (เช่น %)", "Unit (e.g. %)"))
                period_options = [PERIOD_LABELS_TH.get(p, p) for p in PERIODS] if is_thai_mode else PERIODS
                period_display = col2.selectbox(_t("ช่วงเวลา", "Period"), period_options)
                period = PERIODS[[PERIOD_LABELS_TH.get(p, p) for p in PERIODS].index(period_display)] if is_thai_mode else period_display
                desc = st.text_area(_t("คำอธิบาย", "Description"))
                submitted = st.form_submit_button(t("save"))
            if submitted and code and name:
                user = get_current_user()
                with get_sync_db() as db:
                    db.add(QualityIndicator(
                        indicator_code=code, indicator_name=name,
                        category=cat, target_value=target, unit=unit,
                        period=period, description=desc,
                        created_by=user.email if user else "system",
                        updated_by=user.email if user else "system",
                    ))
                st.success(_t("เพิ่มตัวชี้วัดสำเร็จ", "Indicator added."))
                st.rerun()

    # ── Tab 2: Record Entry ───────────────────────────────────────────────────
    with tab2:
        with st.form("record_entry"):
            is_thai_mode = _t("th", "en") == "th"
            ind_options = {
                f"{i.indicator_code} — {INDICATOR_NAMES_TH.get(i.indicator_code, i.indicator_name) if is_thai_mode else i.indicator_name}": i.indicator_code
                for i in indicators
            }
            sel_ind = st.selectbox(_t("ตัวชี้วัด", "Indicator"), list(ind_options.keys()))
            col1, col2, col3 = st.columns(3)
            if is_thai():
                _be_year = col1.number_input("ปี (พ.ศ.)", min_value=2563, max_value=2593,
                                              value=ad_to_be_year(date.today().year))
                year = be_to_ad_year(int(_be_year))
            else:
                year = col1.number_input("Year", min_value=2020, max_value=2050,
                                          value=date.today().year)
            month = col2.number_input(_t("เดือน (0=ข้าม)", "Month (0=skip)"), min_value=0, max_value=12, value=date.today().month)
            actual = col3.number_input(_t("ค่าจริง", "Actual Value"), min_value=0.0, value=0.0)
            notes = st.text_area(_t("หมายเหตุ", "Notes"))
            submitted = st.form_submit_button("📥 " + _t("บันทึก", "Record"))
        if submitted and sel_ind:
            user = get_current_user()
            with get_sync_db() as db:
                db.add(QualityRecord(
                    indicator_id=ind_options[sel_ind],
                    period_year=int(year), period_month=int(month) or None,
                    actual_value=actual, notes=notes,
                    created_by=user.email if user else "system",
                    updated_by=user.email if user else "system",
                ))
            st.success(_t("บันทึกข้อมูลสำเร็จ", "Record saved."))
            st.rerun()

        if records:
            rec_df = pd.DataFrame([{
                _t("ตัวชี้วัด", "Indicator"): r.indicator_id,
                _t("ปี", "Year"): ad_to_be_year(r.period_year) if is_thai() else r.period_year,
                _t("เดือน", "Month"): r.period_month or "",
                _t("ค่าจริง", "Actual"): r.actual_value,
                _t("หมายเหตุ", "Notes"): (r.notes or "")[:60],
            } for r in records])
            st.dataframe(rec_df, use_container_width=True, hide_index=True)

    # ── Tab 3: Trend Charts ───────────────────────────────────────────────────
    with tab3:
        if not records:
            st.info(_t("ยังไม่มีข้อมูล กรุณาบันทึกข้อมูลในแท็บบันทึกข้อมูล", "No records yet. Enter data in the Record Entry tab."))
            return

        is_thai_mode2 = _t("th", "en") == "th"
        ind_options2 = {
            f"{i.indicator_code} — {INDICATOR_NAMES_TH.get(i.indicator_code, i.indicator_name) if is_thai_mode2 else i.indicator_name}": i.indicator_code
            for i in indicators
        }
        sel = st.selectbox(_t("เลือกตัวชี้วัด", "Select Indicator"), list(ind_options2.keys()), key="trend_sel")
        sel_code = ind_options2[sel]

        ind_records = [r for r in records if r.indicator_id == sel_code]
        sel_ind_obj = next((i for i in indicators if i.indicator_code == sel_code), None)

        if ind_records:
            labels = [f"{r.period_year}-{str(r.period_month or 0).zfill(2)}"
                      for r in reversed(ind_records)]
            values = [r.actual_value for r in reversed(ind_records)]
            fig = px.line(x=labels, y=values, markers=True,
                          title=_t(f"แนวโน้ม: {sel}", f"Trend: {sel}"),
                          color_discrete_sequence=["#1e3a5f"])
            if sel_ind_obj and sel_ind_obj.target_value:
                fig.add_hline(y=sel_ind_obj.target_value, line_dash="dash",
                              line_color="green",
                              annotation_text=_t(f"เป้าหมาย: {sel_ind_obj.target_value}", f"Target: {sel_ind_obj.target_value}"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(_t("ยังไม่มีข้อมูลสำหรับตัวชี้วัดนี้", "No records for this indicator."))
