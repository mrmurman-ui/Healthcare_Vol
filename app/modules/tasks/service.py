# -*- coding: utf-8 -*-
"""Task Management — Add/Edit/Delete + Multi-volunteer assignment."""
from __future__ import annotations
from datetime import date, datetime, timedelta, UTC
import streamlit as st
from sqlalchemy import func, select, text
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.tasks.model import Task
from app.modules.volunteers.model import Volunteer
from app.shared.crud_utils import init_crud_state, crud_toolbar, set_edit, set_list
from app.shared.date_utils import be_date_input_col, fmt_date

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en

PRIORITIES = ["low","medium","high","critical"]
STATUSES   = ["new","assigned","in_progress","completed","cancelled","overdue"]
TASK_TYPES = ["home_visit","referral_followup","citizen_followup","community_survey","health_education","medication_delivery"]

STATUS_TH   = {"":"ทั้งหมด","new":"งานใหม่","assigned":"มอบหมายแล้ว","in_progress":"กำลังดำเนินการ","completed":"เสร็จสิ้น","cancelled":"ยกเลิก","overdue":"เกินกำหนด"}
PRIORITY_TH = {"":"ทั้งหมด","low":"ต่ำ","medium":"ปานกลาง","high":"สูง","critical":"วิกฤต"}
TYPE_TH     = {"home_visit":"เยี่ยมบ้าน","referral_followup":"ติดตามการส่งต่อ","citizen_followup":"ติดตามประชาชน","community_survey":"สำรวจชุมชน","health_education":"ให้ความรู้สุขภาพ","medication_delivery":"ส่งยาถึงบ้าน"}
PRIORITY_ICON = {"low":"🟢","medium":"🟡","high":"🟠","critical":"🔴"}

def _sl(d, k): return d.get(k,k) if st.session_state.get("lang","TH")=="TH" else k
def status_label(v): return STATUS_TH.get(v,v) if st.session_state.get("lang","TH")=="TH" else (v or "All")
def priority_label(v): return PRIORITY_TH.get(v,v) if st.session_state.get("lang","TH")=="TH" else (v or "All")


def _ensure_task_volunteers_table():
    """Create task_volunteers join table if not exists."""
    with get_sync_db() as db:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS task_volunteers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                volunteer_id UUID NOT NULL REFERENCES volunteers(id) ON DELETE CASCADE,
                assigned_at TIMESTAMP DEFAULT NOW(),
                note TEXT,
                UNIQUE(task_id, volunteer_id)
            )
        """))


def _get_task_volunteers(task_id: str) -> list:
    with get_sync_db() as db:
        rows = db.execute(text("""
            SELECT v.id, v.full_name, v.volunteer_code
            FROM task_volunteers tv
            JOIN volunteers v ON v.id = tv.volunteer_id
            WHERE tv.task_id = :tid
        """), {"tid": task_id}).fetchall()
    return rows


def _set_task_volunteers(task_id: str, vol_ids: list[str], actor: str):
    with get_sync_db() as db:
        db.execute(text("DELETE FROM task_volunteers WHERE task_id = :tid"), {"tid": task_id})
        for vid in vol_ids:
            db.execute(text("""
                INSERT INTO task_volunteers (id, task_id, volunteer_id)
                VALUES (gen_random_uuid(), :tid, :vid)
                ON CONFLICT DO NOTHING
            """), {"tid": task_id, "vid": vid})


def render_tasks() -> None:
    _ensure_task_volunteers_table()
    st.header("✅ " + _t("การจัดการงาน","Task Management"))
    is_th = st.session_state.get("lang","TH")=="TH"
    init_crud_state("task")
    mode = crud_toolbar("task","งาน","Task")

    if mode == "add":
        st.subheader("➕ " + _t("เพิ่มงานใหม่","Add New Task"))
        _task_form("task_add", None); return

    if mode == "edit":
        eid = st.session_state.get("task_edit_id")
        with get_sync_db() as db: rec = db.get(Task, eid)
        if rec:
            st.subheader("✏️ " + _t(f"แก้ไขงาน: {rec.title}",f"Edit Task: {rec.title}"))
            _task_form("task_edit", rec)
        else:
            st.error(_t("ไม่พบข้อมูล","Not found"))
        return

    # ── Filters ───────────────────────────────────────────────────────────────
    fc1,fc2,fc3,fc4 = st.columns(4)
    f_status   = fc1.selectbox(_t("สถานะ","Status"),    [""]+STATUSES, format_func=status_label, key="tf_s")
    f_priority = fc2.selectbox(_t("ความสำคัญ","Priority"),[""]+PRIORITIES, format_func=priority_label, key="tf_p")
    f_type     = fc3.selectbox(_t("ประเภท","Type"),     [""]+TASK_TYPES, format_func=lambda x: TYPE_TH.get(x,x) if is_th else x, key="tf_t")
    f_search   = fc4.text_input("🔍 " + _t("ค้นหา","Search"), key="tf_q")

    with get_sync_db() as db:
        stmt = select(Task).where(Task.is_deleted == False)
        if f_status:   stmt = stmt.where(Task.status == f_status)
        if f_priority: stmt = stmt.where(Task.priority == f_priority)
        if f_type:     stmt = stmt.where(Task.task_type == f_type)
        if f_search:   stmt = stmt.where(Task.title.ilike(f"%{f_search}%"))
        tasks = db.execute(stmt.order_by(Task.due_date)).scalars().all()

    if not tasks:
        st.info(_t("ยังไม่มีงาน","No tasks found.")); return

    # Summary
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("📋 " + _t("ทั้งหมด","Total"), len(tasks))
    s2.metric("🔴 " + _t("วิกฤต","Critical"), sum(1 for t in tasks if t.priority=="critical"))
    s3.metric("⏳ " + _t("กำลังดำเนินการ","In Progress"), sum(1 for t in tasks if t.status=="in_progress"))
    s4.metric("✅ " + _t("เสร็จสิ้น","Done"), sum(1 for t in tasks if t.status=="completed"))
    st.divider()

    for task in tasks:
        icon = PRIORITY_ICON.get(task.priority,"⚪")
        p_lbl = PRIORITY_TH.get(task.priority,task.priority) if is_th else task.priority
        s_lbl = STATUS_TH.get(task.status,task.status) if is_th else task.status
        t_lbl = TYPE_TH.get(task.task_type,task.task_type) if is_th else task.task_type
        tv = _get_task_volunteers(str(task.id))
        vol_names = ", ".join(v[1] for v in tv) if tv else "—"

        c1,c2,c3,ce,cd = st.columns([5,2,2,1,1])
        c1.markdown(f"{icon} **{task.title}**  \n`{task.task_code}` · {t_lbl}")
        c2.markdown(f"{s_lbl}  \n{fmt_date(task.due_date)}")
        c3.markdown(f"👥 {vol_names[:30]}")
        if ce.button("✏️",key=f"te_{task.id}",help=_t("แก้ไข","Edit")): set_edit("task",task.id)
        if cd.button("🗑️",key=f"td_{task.id}",help=_t("ลบ","Delete")):
            st.session_state[f"task_del_{task.id}"] = True; st.rerun()

        if st.session_state.get(f"task_del_{task.id}"):
            st.warning(_t(f"ยืนยันลบงาน '{task.title}'?",f"Delete task '{task.title}'?"))
            y,n = st.columns(2)
            if y.button("✅",key=f"tdy_{task.id}"):
                with get_sync_db() as db:
                    obj = db.get(Task,str(task.id))
                    if obj: obj.is_deleted = True
                del st.session_state[f"task_del_{task.id}"]
                st.success(_t("ลบแล้ว","Deleted.")); st.rerun()
            if n.button("❌",key=f"tdn_{task.id}"):
                del st.session_state[f"task_del_{task.id}"]; st.rerun()
        st.divider()

    st.caption(_t(f"ทั้งหมด {len(tasks)} งาน",f"Total: {len(tasks)} tasks"))


def _task_form(form_key, rec):
    actor = get_current_user().email if get_current_user() else "system"
    is_th = st.session_state.get("lang","TH")=="TH"

    # Load volunteers for multi-select
    with get_sync_db() as db:
        all_vols = db.execute(select(Volunteer).order_by(Volunteer.full_name)).scalars().all()
        all_cits = db.execute(select(Citizen).order_by(Citizen.full_name).limit(200)).scalars().all()

    vol_opts = {f"{v.full_name} ({v.volunteer_code})": str(v.id) for v in all_vols}
    cit_opts = {f"{c.full_name}": str(c.id) for c in all_cits}

    # Pre-select current volunteers
    cur_vol_names = []
    if rec:
        cur_tv = _get_task_volunteers(str(rec.id))
        cur_vol_ids = [str(v[0]) for v in cur_tv]
        cur_vol_names = [k for k,v in vol_opts.items() if v in cur_vol_ids]

    with st.form(form_key):
        c1,c2 = st.columns(2)
        code  = c1.text_input(_t("รหัสงาน","Task Code"), value=rec.task_code if rec else f"TASK-{date.today().strftime('%Y')}-{__import__('random').randint(10000,99999)}")
        title = c2.text_input(_t("ชื่องาน","Title"), value=rec.title if rec else "")
        desc  = st.text_area(_t("รายละเอียด","Description"), value=rec.description or "" if rec else "")

        c3,c4,c5 = st.columns(3)
        type_idx = TASK_TYPES.index(rec.task_type) if rec and rec.task_type in TASK_TYPES else 0
        ttype = c3.selectbox(_t("ประเภทงาน","Task Type"), TASK_TYPES,
                             index=type_idx, format_func=lambda x: TYPE_TH.get(x,x) if is_th else x)
        prio_idx = PRIORITIES.index(rec.priority) if rec and rec.priority in PRIORITIES else 1
        priority = c4.selectbox(_t("ระดับความสำคัญ","Priority"), PRIORITIES,
                                index=prio_idx, format_func=lambda x: PRIORITY_TH.get(x,x) if is_th else x)
        stat_idx = STATUSES.index(rec.status) if rec and rec.status in STATUSES else 0
        status = c5.selectbox(_t("สถานะ","Status"), STATUSES,
                              index=stat_idx, format_func=lambda x: STATUS_TH.get(x,x) if is_th else x)

        c6,c7 = st.columns(2)
        due = be_date_input_col(c6, _t("วันกำหนดส่ง","Due Date"),
                                value=date.today()+timedelta(days=7),
                                key=form_key+"_due")

        # Multi-volunteer selection
        st.markdown("👥 **" + _t("มอบหมายอาสาสมัคร (เลือกได้หลายคน)","Assign Volunteers (multi-select)") + "**")
        sel_vols = st.multiselect(_t("เลือกอาสาสมัคร","Select Volunteers"),
                                  list(vol_opts.keys()), default=cur_vol_names,
                                  key=form_key+"_vols")

        # Optional citizen link
        cit_label_list = [_t("— ไม่เชื่อมโยง —","— None —")] + list(cit_opts.keys())
        cur_cit_name = _t("— ไม่เชื่อมโยง —","— None —")
        if rec and rec.citizen_id:
            match = [k for k,v in cit_opts.items() if v == str(rec.citizen_id)]
            if match: cur_cit_name = match[0]
        cit_sel = st.selectbox(_t("เชื่อมโยงประชาชน (ไม่บังคับ)","Link Citizen (optional)"),
                               cit_label_list,
                               index=cit_label_list.index(cur_cit_name) if cur_cit_name in cit_label_list else 0,
                               key=form_key+"_cit")

        sub = st.form_submit_button(_t("💾 บันทึก","💾 Save"), type="primary", use_container_width=True)

    if sub and title:
        cit_id = cit_opts.get(cit_sel) if cit_sel and cit_sel not in (_t("— ไม่เชื่อมโยง —","— None —"),) else None
        vol_ids = [vol_opts[v] for v in sel_vols if v in vol_opts]
        # First volunteer name for assigned_to field
        assigned_names = ", ".join(v.split("(")[0].strip() for v in sel_vols) if sel_vols else None

        with get_sync_db() as db:
            if rec:
                obj = db.get(Task, str(rec.id))
                if obj:
                    obj.task_code=code; obj.title=title; obj.description=desc or None
                    obj.task_type=ttype; obj.priority=priority; obj.status=status
                    obj.due_date=str(due); obj.assigned_to=assigned_names
                    obj.citizen_id=cit_id; obj.updated_by=actor
                st.success(_t("แก้ไขสำเร็จ","Updated."))
                task_id = str(rec.id)
            else:
                new_task = Task(task_code=code,title=title,description=desc or None,
                                task_type=ttype,priority=priority,status=status,
                                due_date=str(due),assigned_to=assigned_names,
                                citizen_id=cit_id,created_by=actor,updated_by=actor)
                db.add(new_task)
                db.flush()
                task_id = str(new_task.id)
                st.success(_t("เพิ่มงานสำเร็จ","Task added."))

        _set_task_volunteers(task_id, vol_ids, actor)
        if vol_ids:
            st.info(_t(f"มอบหมายให้ {len(vol_ids)} คน: {assigned_names}",
                       f"Assigned to {len(vol_ids)} volunteer(s): {assigned_names}"))
        set_list("task"); st.rerun()
    elif sub:
        st.warning(_t("กรุณากรอกชื่องาน","Task title is required."))
