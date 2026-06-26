# -*- coding: utf-8 -*-
"""Community Projects — full Thai/EN bilingual."""
from __future__ import annotations
import streamlit as st
from datetime import date
from sqlalchemy import func, select
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.shared.date_utils import be_date_input_col, fmt_date


def _t(th: str, en: str) -> str:
    return th if st.session_state.get("lang","TH") == "TH" else en


class CommunityProject:
    __tablename__ = "community_projects"


TYPE_OPTIONS = {
    "elderly_club":      ("ชมรมผู้สูงอายุ",        "Elderly Club"),
    "exercise_program":  ("โครงการออกกำลังกาย",    "Exercise Program"),
    "home_modification": ("ปรับปรุงที่อยู่อาศัย",   "Home Modification"),
    "community_survey":  ("สำรวจชุมชน",             "Community Survey"),
    "health_activity":   ("กิจกรรมสุขภาพ",          "Health Activity"),
    "other":             ("อื่นๆ",                  "Other"),
}
STATUS_OPTIONS = {
    "active":    ("ดำเนินการ",  "Active"),
    "completed": ("เสร็จสิ้น",  "Completed"),
    "planning":  ("วางแผน",     "Planning"),
    "cancelled": ("ยกเลิก",     "Cancelled"),
}


def render_community_projects() -> None:
    from app.modules.community_projects.model import CommunityProject as CP
    is_thai = st.session_state.get("lang","TH") == "TH"

    with get_sync_db() as db:
        try:
            projects = db.execute(
                select(CP).where(CP.is_deleted == False)
                .order_by(CP.created_at.desc()).limit(100)
            ).scalars().all()
            total     = db.execute(select(func.count()).select_from(CP).where(CP.is_deleted==False)).scalar() or 0
            active    = db.execute(select(func.count()).select_from(CP).where(CP.status=="active",CP.is_deleted==False)).scalar() or 0
            completed = db.execute(select(func.count()).select_from(CP).where(CP.status=="completed",CP.is_deleted==False)).scalar() or 0
            planning  = db.execute(select(func.count()).select_from(CP).where(CP.status=="planning",CP.is_deleted==False)).scalar() or 0
        except Exception as e:
            st.error(f"Database error: {e}")
            return

    # KPIs
    c1,c2,c3,c4 = st.columns(4)
    c1.metric(_t("โครงการทั้งหมด","Total Projects"),  total)
    c2.metric(_t("ดำเนินการ","Active"),               active)
    c3.metric(_t("เสร็จสิ้น","Completed"),            completed)
    c4.metric(_t("วางแผน","Planning"),                planning)

    tab1, tab2 = st.tabs([
        _t("📋 รายการโครงการ","📋 Project List"),
        _t("➕ เพิ่มโครงการ","➕ Add Project"),
    ])

    with tab1:
        if projects:
            import pandas as pd
            df = pd.DataFrame([{
                _t("รหัส","Code"):       p.project_code,
                _t("ชื่อโครงการ","Name"): p.project_name,
                _t("ประเภท","Type"):     TYPE_OPTIONS.get(p.project_type,
                                          (p.project_type,p.project_type))[0 if is_thai else 1],
                _t("สถานะ","Status"):    STATUS_OPTIONS.get(p.status,
                                          (p.status,p.status))[0 if is_thai else 1],
                _t("งบประมาณ (฿)","Budget (฿)"): f"{p.budget:,.0f}" if p.budget else "-",
                _t("ผู้รับผิดชอบ","Owner"): p.owner or "-",
                _t("เริ่ม","Start"):     str(p.start_date or "")[:10],
                _t("สิ้นสุด","End"):     str(p.end_date or "")[:10],
            } for p in projects])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info(_t("ยังไม่มีโครงการ","No projects yet."))

    with tab2:
        with st.form("add_project_form"):
            c1, c2 = st.columns(2)
            code    = c1.text_input(_t("รหัสโครงการ *","Project Code *"))
            name    = c2.text_input(_t("ชื่อโครงการ *","Project Name *"))
            ptype   = c1.selectbox(
                _t("ประเภท","Type"),
                list(TYPE_OPTIONS.keys()),
                format_func=lambda x: TYPE_OPTIONS[x][0 if is_thai else 1]
            )
            status  = c2.selectbox(
                _t("สถานะ","Status"),
                list(STATUS_OPTIONS.keys()),
                format_func=lambda x: STATUS_OPTIONS[x][0 if is_thai else 1]
            )
            desc    = st.text_area(_t("คำอธิบาย","Description"))
            c3, c4  = st.columns(2)
            start   = be_date_input_col(c3, _t("วันที่เริ่ม","Start Date"), value=date.today())
            end     = be_date_input_col(c4, _t("วันที่สิ้นสุด","End Date"), value=date.today())
            budget  = c3.number_input(_t("งบประมาณ (฿)","Budget (฿)"), 0.0, 10000000.0, 0.0, 1000.0)
            owner   = c4.text_input(_t("ผู้รับผิดชอบ","Project Owner"))
            province= c3.text_input(_t("จังหวัด","Province"), value="เชียงใหม่")
            submit  = st.form_submit_button(
                _t("💾 บันทึกโครงการ","💾 Save Project"),
                type="primary", use_container_width=True
            )

        if submit:
            if not code or not name:
                st.error(_t("กรุณากรอกรหัสและชื่อโครงการ","Code and Name are required."))
            else:
                try:
                    actor = get_current_user().email if get_current_user() else "system"
                    with get_sync_db() as db:
                        from app.modules.community_projects.model import CommunityProject as CP2
                        db.add(CP2(
                            project_code=code, project_name=name,
                            project_type=ptype, status=status,
                            description=desc or None,
                            start_date=str(start), end_date=str(end),
                            budget=budget or None, owner=owner or None,
                            province=province or None,
                            created_by=actor, updated_by=actor,
                        ))
                    st.success("✅ " + _t("บันทึกสำเร็จ","Project saved."))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
