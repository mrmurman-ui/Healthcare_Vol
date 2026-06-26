"""Outcome Tracking — longitudinal case outcome tracking."""
from __future__ import annotations

import uuid
from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.localization.service import t
from app.shared.date_utils import fmt_date, be_date_input, be_date_input_col
from app.shared.base_model import UUIDBase


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


OUTCOME_TYPES = ["improved", "stable", "deteriorated", "resolved", "ongoing"]
OUTCOME_STATUS = ["open", "closed", "pending_review"]

OUTCOME_TYPES_TH = {
    "improved": "ดีขึ้น",
    "stable": "คงที่",
    "deteriorated": "แย่ลง",
    "resolved": "หายแล้ว",
    "ongoing": "ต่อเนื่อง",
}
OUTCOME_STATUS_TH = {
    "open": "เปิด",
    "closed": "ปิด",
    "pending_review": "รอตรวจสอบ",
}


# ── Model ─────────────────────────────────────────────────────────────────────

class CaseOutcome(UUIDBase):
    __tablename__ = "case_outcomes"

    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        String(50), index=True, nullable=True
    )
    case_ref: Mapped[str | None] = mapped_column(String(100))
    outcome_type: Mapped[str] = mapped_column(String(50), default="ongoing")
    baseline_value: Mapped[str | None] = mapped_column(String(200))
    current_value: Mapped[str | None] = mapped_column(String(200))
    outcome_status: Mapped[str] = mapped_column(String(30), default="open")
    evaluation_date: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False)


# ── Page ─────────────────────────────────────────────────────────────────────

def render_outcomes() -> None:
    st.header("📊 " + t("nav_outcomes"))

    tab1, tab2 = st.tabs([
        _t("บันทึกผลลัพธ์", "Outcome Records"),
        _t("เพิ่มผลลัพธ์", "Add Outcome"),
    ])

    with tab1:
        is_thai = _t("th", "en") == "th"
        if is_thai:
            type_filter_options = [""] + OUTCOME_TYPES
            type_filter_display = [_t("ทั้งหมด", "All")] + [OUTCOME_TYPES_TH.get(o, o) for o in OUTCOME_TYPES]
            type_sel = st.selectbox(_t("กรองตามผลลัพธ์", "Filter by Outcome"), type_filter_display)
            type_filter = type_filter_options[type_filter_display.index(type_sel)]
        else:
            type_filter = st.selectbox("Filter by Outcome", [""] + OUTCOME_TYPES)

        with get_sync_db() as db:
            stmt = select(CaseOutcome).where(CaseOutcome.is_deleted == False)
            if type_filter:
                stmt = stmt.where(CaseOutcome.outcome_type == type_filter)
            stmt = stmt.order_by(CaseOutcome.created_at.desc()).limit(200)
            outcomes = db.execute(stmt).scalars().all()

        outcome_icons = {
            "improved": "🟢", "stable": "🟡", "deteriorated": "🔴",
            "resolved": "✅", "ongoing": "🔵",
        }

        if outcomes:
            df = pd.DataFrame([{
                _t("ประเภท", "Type"): outcome_icons.get(o.outcome_type, "") + " " + (OUTCOME_TYPES_TH.get(o.outcome_type, o.outcome_type) if is_thai else o.outcome_type),
                _t("อ้างอิงกรณี", "Case Ref"): o.case_ref or "",
                _t("ค่าเริ่มต้น", "Baseline"): o.baseline_value or "",
                _t("ค่าปัจจุบัน", "Current"): o.current_value or "",
                _t("สถานะ", "Status"): OUTCOME_STATUS_TH.get(o.outcome_status, o.outcome_status) if is_thai else o.outcome_status,
                _t("วันที่ประเมิน", "Eval Date"): fmt_date(o.evaluation_date),
                _t("หมายเหตุ", "Notes"): (o.notes or "")[:60],
            } for o in outcomes])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Summary
            col1, col2, col3, col4, col5 = st.columns(5)
            from collections import Counter
            counts = Counter(o.outcome_type for o in outcomes)
            col1.metric("🟢 " + _t("ดีขึ้น", "Improved"), counts.get("improved", 0))
            col2.metric("🟡 " + _t("คงที่", "Stable"), counts.get("stable", 0))
            col3.metric("🔴 " + _t("แย่ลง", "Deteriorated"), counts.get("deteriorated", 0))
            col4.metric("✅ " + _t("หายแล้ว", "Resolved"), counts.get("resolved", 0))
            col5.metric("🔵 " + _t("ต่อเนื่อง", "Ongoing"), counts.get("ongoing", 0))
        else:
            st.info(_t("ยังไม่มีการบันทึกผลลัพธ์", "No outcomes recorded yet."))

    with tab2:
        # Search citizen
        search = st.text_input(_t("ค้นหาประชาชน (ไม่บังคับ)", "Search Citizen (optional)"), key="out_search")
        citizen_id = None
        if search:
            with get_sync_db() as db:
                citizens = db.execute(
                    select(Citizen).where(Citizen.full_name.ilike(f"%{search}%")).limit(20)
                ).scalars().all()
            if citizens:
                opts = {f"{c.full_name}": str(c.id) for c in citizens}
                sel = st.selectbox(_t("เลือกประชาชน", "Select Citizen"), list(opts.keys()))
                citizen_id = opts[sel]

        is_thai = _t("th", "en") == "th"
        outcome_display = [OUTCOME_TYPES_TH.get(o, o) for o in OUTCOME_TYPES] if is_thai else OUTCOME_TYPES
        status_display = [OUTCOME_STATUS_TH.get(s, s) for s in OUTCOME_STATUS] if is_thai else OUTCOME_STATUS

        with st.form("add_outcome"):
            col1, col2 = st.columns(2)
            case_ref = col1.text_input(_t("อ้างอิงกรณี", "Case Reference"))
            outcome_sel = col2.selectbox(_t("ประเภทผลลัพธ์", "Outcome Type"), outcome_display)
            outcome_type = OUTCOME_TYPES[outcome_display.index(outcome_sel)] if is_thai else outcome_sel
            baseline = col1.text_input(_t("ค่าเริ่มต้น", "Baseline Value"))
            current = col2.text_input(_t("ค่าปัจจุบัน", "Current Value"))
            eval_date = be_date_input_col(col1, _t("วันที่ประเมิน", "Evaluation Date"), value=date.today())
            status_sel = col2.selectbox(_t("สถานะ", "Status"), status_display)
            status = OUTCOME_STATUS[status_display.index(status_sel)] if is_thai else status_sel
            notes = st.text_area(_t("หมายเหตุ", "Notes"))
            submitted = st.form_submit_button("💾 " + t("save"))

        if submitted:
            user = get_current_user()
            with get_sync_db() as db:
                db.add(CaseOutcome(
                    citizen_id=citizen_id,
                    case_ref=case_ref or None,
                    outcome_type=outcome_type,
                    baseline_value=baseline or None,
                    current_value=current or None,
                    outcome_status=status,
                    evaluation_date=str(eval_date),
                    notes=notes or None,
                    created_by=user.email if user else "system",
                    updated_by=user.email if user else "system",
                ))
            st.success(_t("บันทึกผลลัพธ์สำเร็จ", "Outcome recorded."))
            st.rerun()
