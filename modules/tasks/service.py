# -*- coding: utf-8 -*-
"""Task Management — full Thai/EN bilingual."""
from __future__ import annotations
from datetime import date, timedelta
import streamlit as st
from sqlalchemy import func, select
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.tasks.model import Task
from app.modules.volunteers.model import Volunteer
from app.shared.date_utils import be_date_input_col, fmt_date


def _t(th: str, en: str) -> str:
    return th if st.session_state.get("lang", "TH") == "TH" else en


PRIORITIES = ["low", "medium", "high", "critical"]
STATUSES   = ["new", "assigned", "in_progress", "completed", "cancelled", "overdue"]
TASK_TYPES = [
    "home_visit", "referral_followup", "citizen_followup",
    "community_survey", "health_education", "medication_delivery",
]

STATUS_TH = {
    "":           "ทั้งหมด",
    "new":        "งานใหม่",
    "assigned":   "มอบหมายแล้ว",
    "in_progress":"กำลังดำเนินการ",
    "completed":  "เสร็จสิ้น",
    "cancelled":  "ยกเลิก",
    "overdue":    "เกินกำหนด",
}
PRIORITY_TH = {
    "":         "ทั้งหมด",
    "low":      "ต่ำ",
    "medium":   "ปานกลาง",
    "high":     "สูง",
    "critical": "วิกฤต",
}
TYPE_TH = {
    "home_visit":         "เยี่ยมบ้าน",
    "referral_followup":  "ติดตามการส่งต่อ",
    "citizen_followup":   "ติดตามประชาชน",
    "community_survey":   "สำรวจชุมชน",
    "health_education":   "ให้ความรู้สุขภาพ",
    "medication_delivery":"ส่งยาถึงบ้าน",
}

def _sl(d: dict, key: str) -> str:
    """Return Thai or EN label from a dict."""
    is_thai = st.session_state.get("lang","TH") == "TH"
    return d[key] if is_thai else key

def status_label(v: str) -> str:
    is_thai = st.session_state.get("lang","TH") == "TH"
    return STATUS_TH.get(v, v) if is_thai else (v or "All")

def priority_label(v: str) -> str:
    is_thai = st.session_state.get("lang","TH") == "TH"
    return PRIORITY_TH.get(v, v) if is_thai else (v or "All")

def type_label(v: str) -> str:
    is_thai = st.session_state.get("lang","TH") == "TH"
    return TYPE_TH.get(v, v) if is_thai else v


PRIORITY_EMOJI = {"low":"🟡","medium":"🟠","high":"🔴","critical":"🚨"}


def render_tasks() -> None:
    is_thai = st.session_state.get("lang","TH") == "TH"

    # ── KPI row ───────────────────────────────────────────────────────────────
    with get_sync_db() as db:
        try:
            rows = db.execute(
                select(Task.status, func.count())
                .where(Task.is_deleted == False)
                .group_by(Task.status)
            ).all()
            sm = {r[0]: r[1] for r in rows}
        except Exception:
            sm = {}

    total    = sum(sm.values())
    done     = sm.get("completed", 0)
    pending  = sm.get("new",0) + sm.get("assigned",0) + sm.get("in_progress",0)
    overdue  = sm.get("overdue", 0)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric(_t("งานทั้งหมด","Total Tasks"),        total)
    c2.metric(_t("เสร็จสิ้น","Completed"),           done,
              delta=f"{round(done/max(total,1)*100,1)}%")
    c3.metric(_t("รอดำเนินการ","Pending"),           pending)
    c4.metric(_t("เกินกำหนด","Overdue"),             overdue,
              delta=f"-{overdue}" if overdue else None,
              delta_color="inverse" if overdue else "off")

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    sel_status   = col1.selectbox(
        _t("สถานะ","Status"),
        [""] + STATUSES,
        format_func=lambda v: STATUS_TH.get(v, v) if is_thai else (v or _t("ทั้งหมด","All")),
        key="task_status",
    )
    sel_priority = col2.selectbox(
        _t("ลำดับความสำคัญ","Priority"),
        [""] + PRIORITIES,
        format_func=lambda v: PRIORITY_TH.get(v, v) if is_thai else (v or _t("ทั้งหมด","All")),
        key="task_priority",
    )
    search = col3.text_input(_t("ค้นหา","Search"), key="task_search")

    # ── Task list ─────────────────────────────────────────────────────────────
    with get_sync_db() as db:
        try:
            stmt = select(Task).where(Task.is_deleted == False)
            if sel_status:
                stmt = stmt.where(Task.status == sel_status)
            if sel_priority:
                stmt = stmt.where(Task.priority == sel_priority)
            if search:
                stmt = stmt.where(Task.title.ilike(f"%{search}%"))
            tasks = db.execute(stmt.order_by(Task.due_date).limit(200)).scalars().all()
        except Exception as e:
            st.error(f"Database error: {e}")
            tasks = []

    if tasks:
        import pandas as pd
        df = pd.DataFrame([{
            _t("รหัส","Code"):          tk.task_code or "-",
            _t("หัวข้องาน","Title"):    tk.title,
            _t("ประเภท","Type"):        TYPE_TH.get(tk.task_type or "", tk.task_type or "-") if is_thai else (tk.task_type or "-"),
            _t("ลำดับ","Priority"):     PRIORITY_EMOJI.get(tk.priority,"") + " " + (PRIORITY_TH.get(tk.priority or "","") if is_thai else (tk.priority or "")),
            _t("สถานะ","Status"):       STATUS_TH.get(tk.status or "", tk.status or "") if is_thai else (tk.status or ""),
            _t("วันกำหนด","Due Date"):  fmt_date(tk.due_date),
        } for tk in tasks])
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ " + _t("ส่งออก CSV","Export CSV"),
            csv, "tasks.csv", "text/csv"
        )
    else:
        st.info(_t("ไม่พบงาน","No tasks found."))

    st.divider()

    # ── Update status ─────────────────────────────────────────────────────────
    with st.expander("✏️ " + _t("อัพเดทสถานะงาน","Update Task Status")):
        if tasks:
            opts = {f"{tk.task_code} — {tk.title[:40]}": tk.id for tk in tasks}
            sel  = st.selectbox(_t("เลือกงาน","Select Task"), list(opts.keys()))
            new_st = st.selectbox(
                _t("สถานะใหม่","New Status"),
                STATUSES,
                format_func=lambda v: STATUS_TH.get(v, v) if is_thai else v
            )
            if st.button(_t("✔ บันทึก","✔ Update"), type="primary"):
                try:
                    actor = get_current_user().email if get_current_user() else "system"
                    with get_sync_db() as db:
                        t2 = db.get(Task, opts[sel])
                        if t2:
                            t2.status = new_st
                            t2.updated_by = actor
                    st.success("✅ " + _t("อัพเดทแล้ว","Status updated."))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── Add new task ──────────────────────────────────────────────────────────
    with st.expander("➕ " + _t("สร้างงานใหม่","Create New Task")):
        with st.form("new_task_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            title    = c1.text_input(_t("หัวข้องาน *","Task Title *"))
            task_type = c2.selectbox(
                _t("ประเภทงาน","Task Type"), TASK_TYPES,
                format_func=lambda v: TYPE_TH.get(v,v) if is_thai else v
            )
            c3, c4 = st.columns(2)
            priority = c3.selectbox(
                _t("ลำดับความสำคัญ","Priority"), PRIORITIES, index=1,
                format_func=lambda v: PRIORITY_TH.get(v,v) if is_thai else v
            )
            due_date = be_date_input_col(c4, 
                _t("วันกำหนด","Due Date"),
                value=date.today() + timedelta(days=7)
            )

            # Citizen picker
            with get_sync_db() as db:
                citizens = db.execute(select(Citizen).limit(100)).scalars().all()
                vols     = db.execute(select(Volunteer).limit(100)).scalars().all()
            cit_opts = {_t("ไม่ระบุ","None"): None}
            cit_opts.update({c.full_name: c.id for c in citizens})
            vol_opts = {_t("ไม่ระบุ","None"): None}
            vol_opts.update({v.full_name: v.id for v in vols})

            c5, c6 = st.columns(2)
            sel_cit = c5.selectbox(_t("ประชาชน (ไม่บังคับ)","Citizen (optional)"), list(cit_opts.keys()))
            sel_vol = c6.selectbox(_t("อสม. (ไม่บังคับ)","Volunteer (optional)"), list(vol_opts.keys()))
            desc    = st.text_area(_t("คำอธิบาย","Description"), height=80)

            submitted = st.form_submit_button(
                _t("💾 สร้างงาน","💾 Create Task"),
                type="primary", use_container_width=True
            )

        if submitted:
            if not title:
                st.error(_t("กรุณากรอกหัวข้องาน","Please enter a task title."))
            else:
                try:
                    import secrets
                    actor = get_current_user().email if get_current_user() else "system"
                    with get_sync_db() as db:
                        code = f"TASK{secrets.token_hex(3).upper()}"
                        assigned_to = vol_opts.get(sel_vol)
                        db.add(Task(
                            task_code=code, title=title,
                            task_type=task_type, priority=priority,
                            status="new" if not assigned_to else "assigned",
                            due_date=str(due_date),
                            citizen_id=cit_opts.get(sel_cit),
                            volunteer_id=assigned_to,
                            description=desc or None,
                            created_by=actor, updated_by=actor,
                        ))
                    st.success(f"✅ {_t('สร้างงาน','Task created')}: {code}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
