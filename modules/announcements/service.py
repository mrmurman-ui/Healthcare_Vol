"""Announcements module."""
from __future__ import annotations


def _t(th: str, en: str) -> str:
    import streamlit as _st
    return th if _st.session_state.get("lang", "TH") == "TH" else en


from datetime import date

import streamlit as st
from sqlalchemy import String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.shared.date_utils import fmt_date, be_date_input, be_date_input_col
from app.shared.base_model import UUIDBase

ANNOUNCEMENT_TYPES = ["community_news", "health_campaign", "emergency_alert", "volunteer_notice"]

# Thai display labels (stored values remain English in DB)
ANNOUNCEMENT_TYPES_TH = {
    "community_news":   "ข่าวชุมชน",
    "health_campaign":  "แคมเปญสุขภาพ",
    "emergency_alert":  "แจ้งเตือนฉุกเฉิน",
    "volunteer_notice": "ประกาศอาสาสมัคร",
}


# ── Model ─────────────────────────────────────────────────────────────────────

class Announcement(UUIDBase):
    __tablename__ = "announcements"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    announcement_type: Mapped[str] = mapped_column(String(50), default="community_news")
    target_province: Mapped[str | None] = mapped_column(String(100))
    target_district: Mapped[str | None] = mapped_column(String(100))
    target_subdistrict: Mapped[str | None] = mapped_column(String(100))
    target_village: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[str | None] = mapped_column(String(20))
    end_date: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(default=True)


# ── Page ─────────────────────────────────────────────────────────────────────

def render_announcements() -> None:
    st.header("📢 " + t("nav_announcements"))

    is_thai = _t("th", "en") == "th"

    # Filter dropdown — show Thai labels in Thai mode
    type_filter_options = [""] + ANNOUNCEMENT_TYPES
    type_filter_display = [_t("ทั้งหมด", "ทั้งหมด")] + (
        [ANNOUNCEMENT_TYPES_TH.get(tp, tp) for tp in ANNOUNCEMENT_TYPES]
        if is_thai else ANNOUNCEMENT_TYPES
    )
    type_sel = st.selectbox(_t("ประเภท", "Type"), type_filter_display)
    type_filter = type_filter_options[type_filter_display.index(type_sel)]

    with get_sync_db() as db:
        stmt = select(Announcement).where(Announcement.is_active == True)
        if type_filter:
            stmt = stmt.where(Announcement.announcement_type == type_filter)
        stmt = stmt.order_by(Announcement.created_at.desc())
        announcements = db.execute(stmt).scalars().all()

    type_icons = {
        "emergency_alert":  "🚨",
        "health_campaign":  "💊",
        "volunteer_notice": "👥",
        "community_news":   "📰",
    }

    if announcements:
        for ann in announcements:
            icon = type_icons.get(ann.announcement_type, "📢")
            type_label = ANNOUNCEMENT_TYPES_TH.get(ann.announcement_type, ann.announcement_type) if is_thai else ann.announcement_type
            with st.expander(f"{icon} {ann.title} — {fmt_date(ann.start_date)}"):
                st.write(ann.content or "")
                target_label = ann.target_province or _t("ทุกพื้นที่", "All")
                st.caption(
                    _t(f"ประเภท: {type_label} | พื้นที่: {target_label}",
                       f"Type: {type_label} | Target: {target_label}")
                )
    else:
        st.info(_t("ไม่มีประกาศ", "No announcements."))

    st.divider()
    with st.expander("➕ " + _t("เพิ่มประกาศ", "Add Announcement")):
        with st.form("add_announcement"):
            title = st.text_input(_t("หัวข้อ", "Title"))
            content = st.text_area(_t("เนื้อหา", "Content"))

            # Type selectbox with Thai labels
            ann_type_display = [ANNOUNCEMENT_TYPES_TH.get(tp, tp) for tp in ANNOUNCEMENT_TYPES] if is_thai else ANNOUNCEMENT_TYPES
            ann_type_sel = st.selectbox(_t("ประเภท", "Type"), ann_type_display)
            ann_type = ANNOUNCEMENT_TYPES[ann_type_display.index(ann_type_sel)]

            col1, col2 = st.columns(2)
            start = be_date_input_col(col1, _t("วันที่เริ่ม", "Start Date"), value=date.today())
            end = be_date_input_col(col2, _t("วันที่สิ้นสุด", "End Date"))
            province = st.text_input(_t("จังหวัดเป้าหมาย (เว้นว่าง = ทุกพื้นที่)", "Target Province (blank = all)"))
            submitted = st.form_submit_button(t("save"))

        if submitted and title:
            user = get_current_user()
            actor = user.email if user else "system"
            with get_sync_db() as db:
                db.add(Announcement(
                    title=title, content=content,
                    announcement_type=ann_type,
                    start_date=str(start),
                    end_date=str(end) if end else None,
                    target_province=province or None,
                    created_by=actor, updated_by=actor,
                ))
            st.success(_t("เผยแพร่ประกาศสำเร็จ", "Announcement published."))
            st.rerun()
