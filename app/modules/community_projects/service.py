"""Community Projects — Add / Edit / Delete with full Thai/EN bilingual."""
from __future__ import annotations
from datetime import date
import streamlit as st
from sqlalchemy import select, text, String, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.shared.base_model import UUIDBase
from app.shared.crud_utils import init_crud_state, crud_toolbar, set_edit, set_list
from app.shared.date_utils import fmt_date, be_date_input_col

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en

class CommunityProject(UUIDBase):
    __tablename__ = "community_projects"
    project_code: Mapped[str]         = mapped_column(String(50), unique=True, index=True)
    project_name: Mapped[str]         = mapped_column(String(300), nullable=False)
    project_type: Mapped[str | None]  = mapped_column(String(50))
    description:  Mapped[str | None]  = mapped_column(Text)
    status:       Mapped[str | None]  = mapped_column(String(20), default="planning")
    start_date:   Mapped[str | None]  = mapped_column(String(20))
    end_date:     Mapped[str | None]  = mapped_column(String(20))
    budget:       Mapped[float | None]= mapped_column(Float)
    owner:        Mapped[str | None]  = mapped_column(String(200))
    province:     Mapped[str | None]  = mapped_column(String(100))
    district:     Mapped[str | None]  = mapped_column(String(100))
    notes:        Mapped[str | None]  = mapped_column(Text)
    is_deleted:   Mapped[bool]        = mapped_column(default=False)
    # actual_cost and participant_count added via _ensure_extra_columns() migration

PROJ_TYPES = ["elderly_club","exercise_program","home_modification","community_survey","health_activity","other"]
PROJ_TYPES_TH = {"elderly_club":"ชมรมผู้สูงอายุ","exercise_program":"โปรแกรมออกกำลังกาย","home_modification":"ปรับปรุงบ้าน","community_survey":"สำรวจชุมชน","health_activity":"กิจกรรมสุขภาพ","other":"อื่นๆ"}
PROJ_STATUSES = ["planning","active","completed","cancelled"]
PROJ_STATUS_TH = {"planning":"วางแผน","active":"กำลังดำเนินการ","completed":"เสร็จสิ้น","cancelled":"ยกเลิก"}
STATUS_ICON = {"planning":"🔵","active":"🟢","completed":"✅","cancelled":"⚫"}


def _ensure_extra_columns():
    """Safely add optional columns to community_projects if they don't exist."""
    with get_sync_db() as db:
        for col, coltype in [("actual_cost", "FLOAT"), ("participant_count", "INTEGER")]:
            try:
                db.execute(text(
                    f"ALTER TABLE community_projects ADD COLUMN IF NOT EXISTS {col} {coltype}"
                ))
            except Exception:
                pass


def render_community_projects() -> None:
    _ensure_extra_columns()
    st.header("🏘️ " + t("nav_community_projects"))
    init_crud_state("cp")
    mode = crud_toolbar("cp","โครงการ","Project")
    is_th = st.session_state.get("lang","TH")=="TH"

    if mode == "add":
        st.subheader("➕ " + _t("เพิ่มโครงการ","Add Project"))
        _proj_form("cp_add", None); return

    if mode == "edit":
        eid = st.session_state.get("cp_edit_id")
        with get_sync_db() as db: rec = db.get(CommunityProject, eid)
        if rec:
            st.subheader("✏️ " + _t(f"แก้ไข: {rec.project_name}",f"Edit: {rec.project_name}"))
            _proj_form("cp_edit", rec)
        else:
            st.error(_t("ไม่พบข้อมูล","Not found"))
        return

    f1,f2 = st.columns(2)
    _is_th_cp = st.session_state.get("lang","TH")=="TH"
    f_status = f1.selectbox(
        _t("สถานะ","Status"),
        [""]+PROJ_STATUSES,
        format_func=lambda x: (_t("ทั้งหมด","All") if not x
                                else (PROJ_STATUS_TH.get(x,x) if _is_th_cp else x))
    )
    f_type = f2.selectbox(
        _t("ประเภท","Type"),
        [""]+PROJ_TYPES,
        format_func=lambda x: (_t("ทั้งหมด","All") if not x
                                else (PROJ_TYPES_TH.get(x,x) if _is_th_cp else x))
    )

    with get_sync_db() as db:
        where_parts = ["is_deleted = false"]
        params = {}
        if f_status:
            where_parts.append("status = :status"); params["status"] = f_status
        if f_type:
            where_parts.append("project_type = :ptype"); params["ptype"] = f_type
        where_sql = " AND ".join(where_parts)
        rows = db.execute(text(f"""
            SELECT id, project_code, project_name, project_type, status,
                   start_date, end_date, budget, owner, district,
                   COALESCE(actual_cost, 0) as actual_cost,
                   COALESCE(participant_count, 0) as participant_count
            FROM community_projects
            WHERE {where_sql}
            ORDER BY start_date DESC
        """), params).fetchall()

    if rows:
        for row in rows:
            pid, pcode, pname, ptype, pstatus = row[0], row[1], row[2], row[3], row[4]
            pstart, pend, pbudget, powner, pdistrict = row[5], row[6], row[7], row[8], row[9]
            pactual, pparticipants = row[10], row[11]
            icon = STATUS_ICON.get(pstatus,"⚪")
            s_lbl = PROJ_STATUS_TH.get(pstatus, pstatus) if is_th else pstatus
            t_lbl = PROJ_TYPES_TH.get(ptype, ptype or "") if is_th else (ptype or "")
            c1,c2,c3,ce,cd = st.columns([4,2,2,1,1])
            c1.markdown(f"{icon} **{pname}**  \n`{pcode}` · {t_lbl}")
            c2.markdown(f"{s_lbl}  \n{fmt_date(pstart)} – {fmt_date(pend)}")
            budget_disp = f"฿{pbudget:,.0f}" if pbudget else "—"
            c3.markdown(f"💰 {budget_disp}  \n{powner or '—'}")
            if ce.button("✏️",key=f"ce_{pid}",help=_t("แก้ไข","Edit")): set_edit("cp", pid)
            if cd.button("🗑️",key=f"cd_{pid}",help=_t("ลบ","Delete")):
                st.session_state[f"cp_del_{pid}"] = True; st.rerun()
            if st.session_state.get(f"cp_del_{pid}"):
                st.warning(_t(f"ยืนยันลบ '{pname}'?",f"Delete '{pname}'?"))
                y,n = st.columns(2)
                if y.button("✅",key=f"cdy_{pid}"):
                    with get_sync_db() as db:
                        db.execute(text("UPDATE community_projects SET is_deleted=true WHERE id=:id"), {"id": str(pid)})
                    del st.session_state[f"cp_del_{pid}"]
                    st.success(_t("ลบแล้ว","Deleted.")); st.rerun()
                if n.button("❌",key=f"cdn_{pid}"):
                    del st.session_state[f"cp_del_{pid}"]; st.rerun()
            st.divider()
        st.caption(_t(f"ทั้งหมด {len(rows)} โครงการ",f"Total: {len(rows)} projects"))
    else:
        st.info(_t("ยังไม่มีโครงการ","No projects found."))


def _proj_form(form_key, rec):
    actor = get_current_user().email if get_current_user() else "system"
    is_th = st.session_state.get("lang","TH")=="TH"
    with st.form(form_key):
        c1,c2 = st.columns(2)
        code = c1.text_input(_t("รหัสโครงการ","Project Code"), value=rec.project_code if rec else "")
        name = c2.text_input(_t("ชื่อโครงการ","Project Name"), value=rec.project_name if rec else "")
        cur_type = rec.project_type if rec and rec.project_type in PROJ_TYPES else PROJ_TYPES[0]
        cur_stat = rec.status if rec and rec.status in PROJ_STATUSES else PROJ_STATUSES[0]
        c3,c4 = st.columns(2)
        ptype = c3.selectbox(_t("ประเภทโครงการ","Type"), PROJ_TYPES,
                             index=PROJ_TYPES.index(cur_type),
                             format_func=lambda x: PROJ_TYPES_TH.get(x,x) if is_th else x)
        status = c4.selectbox(_t("สถานะ","Status"), PROJ_STATUSES,
                              index=PROJ_STATUSES.index(cur_stat),
                              format_func=lambda x: PROJ_STATUS_TH.get(x,x) if is_th else x)
        c5,c6 = st.columns(2)
        start = be_date_input_col(c5, _t("วันเริ่มต้น","Start Date"), value=date.today(), key=form_key+"_s")
        end   = be_date_input_col(c6, _t("วันสิ้นสุด","End Date"),   value=date.today(), key=form_key+"_e")
        c7,c8,c9 = st.columns(3)
        budget = c7.number_input(_t("งบประมาณ (บาท)","Budget (THB)"), value=float(rec.budget or 0) if rec else 0.0, min_value=0.0)
        actual_cost = c8.number_input(_t("ค่าใช้จ่ายจริง","Actual Cost"), value=float(rec.actual_cost or 0) if rec else 0.0, min_value=0.0)
        participants = c9.number_input(_t("ผู้เข้าร่วม","Participants"), value=int(rec.participant_count or 0) if rec else 0, min_value=0)
        c10,c11 = st.columns(2)
        owner    = c10.text_input(_t("ผู้รับผิดชอบ","Owner"), value=rec.owner or "" if rec else "")
        district = c11.text_input(_t("อำเภอ","District"), value=rec.district or "" if rec else "")
        desc  = st.text_area(_t("รายละเอียด","Description"), value=rec.description or "" if rec else "")
        notes = st.text_area(_t("หมายเหตุ","Notes"), value=rec.notes or "" if rec else "")
        sub = st.form_submit_button(_t("💾 บันทึก","💾 Save"), type="primary", use_container_width=True)
    if sub and code and name:
        with get_sync_db() as db:
            if rec:
                obj = db.get(CommunityProject,str(rec.id))
                if obj:
                    obj.project_code=code; obj.project_name=name; obj.project_type=ptype
                    obj.status=status; obj.start_date=str(start); obj.end_date=str(end)
                    obj.budget=budget or None; obj.owner=owner or None
                    obj.district=district or None; obj.description=desc or None
                    obj.notes=notes or None; obj.updated_by=actor
                    # Extra columns via raw SQL
                    try:
                        db.execute(text("""
                            UPDATE community_projects SET actual_cost=:ac, participant_count=:pc
                            WHERE id=:rid
                        """), {"ac": actual_cost or None, "pc": participants or None, "rid": str(rec.id)})
                    except Exception: pass
                st.success(_t("แก้ไขสำเร็จ","Updated."))
            else:
                db.add(CommunityProject(project_code=code,project_name=name,project_type=ptype,
                                        status=status,start_date=str(start),end_date=str(end),
                                        budget=budget or None,owner=owner or None,
                                        district=district or None,description=desc or None,
                                        notes=notes or None,created_by=actor,updated_by=actor))
                db.flush()
                # Set extra columns via raw SQL (safe if columns added by migration)
                try:
                    db.execute(text("""
                        UPDATE community_projects SET actual_cost=:ac, participant_count=:pc
                        WHERE project_code=:code
                    """), {"ac": actual_cost or None, "pc": participants or None, "code": code})
                except Exception: pass
                st.success(_t("เพิ่มโครงการสำเร็จ","Project added."))
        set_list("cp"); st.rerun()
    elif sub:
        st.warning(_t("กรุณากรอกรหัสและชื่อโครงการ","Code and name are required."))
