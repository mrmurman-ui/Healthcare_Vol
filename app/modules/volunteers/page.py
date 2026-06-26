"""Volunteers (อสม.) — List · Profile · Add / Edit / Delete — Thai/EN bilingual."""
import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.localization.service import t
from app.modules.volunteers.model import Volunteer
from app.modules.volunteers.profile import render_volunteer_profile
from app.shared.crud_utils import init_crud_state, set_edit, set_list
from app.shared.enum_labels import volunteer_status_labels
from app.shared.enums import VolunteerStatus

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en
PAGE_SIZE = 50


def render_volunteers() -> None:
    st.header(t("nav_volunteers"))

    # ── Profile view ──────────────────────────────────────────────────────────
    if st.session_state.get("vol_profile_id"):
        render_volunteer_profile(st.session_state["vol_profile_id"])
        return

    init_crud_state("vol")
    mode = st.session_state.get("vol_mode", "list")

    # ── ADD ───────────────────────────────────────────────────────────────────
    if mode == "add":
        if st.button("← " + _t("ย้อนกลับ","Back"), key="vol_back_add"):
            set_list("vol")
        st.subheader("➕ " + _t("เพิ่มอาสาสมัคร","Add Volunteer"))
        _vol_form("vol_add", None)
        return

    # ── EDIT ──────────────────────────────────────────────────────────────────
    if mode == "edit":
        if st.button("← " + _t("ย้อนกลับ","Back"), key="vol_back_edit"):
            set_list("vol")
        eid = st.session_state.get("vol_edit_id")
        with get_sync_db() as db:
            rec = db.get(Volunteer, eid)
        if rec:
            st.subheader("✏️ " + _t(f"แก้ไข: {rec.full_name}",f"Edit: {rec.full_name}"))
            _vol_form("vol_edit", rec)
        else:
            st.error(_t("ไม่พบข้อมูล","Not found"))
        return

    # ── LIST ──────────────────────────────────────────────────────────────────
    vsl = volunteer_status_labels()
    is_th = st.session_state.get("lang","TH") == "TH"

    # Filters
    fc1,fc2,fc3 = st.columns([3,2,2])
    f_query  = fc1.text_input("🔍 " + _t("ค้นหาชื่อ/รหัส","Search Name/Code"), key="vol_q")
    f_dist   = fc2.text_input(_t("อำเภอ","District"), key="vol_dist")
    s_opts   = [""] + [e.value for e in VolunteerStatus]
    s_disp   = [_t("ทุกสถานะ","All")] + [vsl.get(s,s) for s in s_opts[1:]]
    f_stat   = s_opts[fc3.selectbox(_t("สถานะ","Status"), range(len(s_disp)),
                                     format_func=lambda i: s_disp[i], key="vol_stat")]

    with get_sync_db() as db:
        stmt = select(Volunteer)
        if f_query:
            stmt = stmt.where(
                Volunteer.full_name.ilike(f"%{f_query}%") |
                Volunteer.volunteer_code.ilike(f"%{f_query}%")
            )
        if f_dist:
            stmt = stmt.where(Volunteer.district.ilike(f"%{f_dist}%"))
        if f_stat:
            stmt = stmt.where(Volunteer.status == f_stat)
        vols = db.execute(stmt.order_by(Volunteer.full_name)).scalars().all()

    total = len(vols)
    # Summary
    s1,s2,s3 = st.columns(3)
    s1.metric(_t("ทั้งหมด","Total"),   total)
    s2.metric("🟢 " + _t("ใช้งาน","Active"),
              sum(1 for v in vols if (v.status or "").lower()=="active"))
    s3.metric("⚫ " + _t("ไม่ใช้งาน","Inactive"),
              sum(1 for v in vols if (v.status or "").lower()!="active"))

    if total == 0:
        st.info(_t("ยังไม่มีข้อมูลอาสาสมัคร","No volunteers found."))
    else:
        # Pagination
        total_pages = max(1,(total+PAGE_SIZE-1)//PAGE_SIZE)
        page = max(1,min(st.session_state.get("vol_page",1),total_pages))
        pc1,pc2,pc3 = st.columns([1,4,1])
        if pc1.button("◀", disabled=page<=1, key="vol_prev"):
            st.session_state["vol_page"]=page-1; st.rerun()
        pc2.markdown(
            f"<div style='text-align:center;padding-top:6px'>"
            f"{_t('หน้า','Page')} <b>{page}</b>/{total_pages} "
            f"({total} {_t('คน','records')})</div>",
            unsafe_allow_html=True
        )
        if pc3.button("▶", disabled=page>=total_pages, key="vol_next"):
            st.session_state["vol_page"]=page+1; st.rerun()

        # DataFrame
        start = (page-1)*PAGE_SIZE
        page_vols = vols[start:start+PAGE_SIZE]
        rows = []
        for v in page_vols:
            s_lbl = vsl.get(v.status or "", v.status or "")
            rows.append({
                "id": str(v.id),
                _t("รหัส อสม.","Code"):         v.volunteer_code,
                _t("ชื่อ-นามสกุล","Full Name"): v.full_name,
                _t("ตำแหน่ง","Position"):        v.position or "—",
                _t("อำเภอ","District"):           v.district or "—",
                _t("โทรศัพท์","Phone"):           v.phone or "—",
                _t("สถานะ","Status"):             ("🟢 " if (v.status or "").lower()=="active" else "⚫ ") + s_lbl,
            })

        df = pd.DataFrame(rows)
        st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
        st.divider()

        # Action panel
        st.markdown("#### " + _t("ดูโปรไฟล์ / แก้ไข / ลบ","View Profile / Edit / Delete"))
        name_opts = {f"{v.volunteer_code}  {v.full_name}": str(v.id) for v in page_vols}
        sel_lbl   = st.selectbox(_t("เลือกอาสาสมัคร","Select Volunteer"),
                                  list(name_opts.keys()), key="vol_sel")
        sel_id    = name_opts.get(sel_lbl)

        a1,a2,a3 = st.columns(3)
        if a1.button("👤 "+_t("ดูโปรไฟล์","View Profile"),
                     key="vol_do_prof", use_container_width=True):
            if sel_id:
                st.session_state["vol_profile_id"] = sel_id; st.rerun()

        if a2.button("✏️ "+_t("แก้ไข","Edit"),
                     key="vol_do_edit", use_container_width=True, type="primary"):
            if sel_id: set_edit("vol", sel_id)

        if a3.button("🗑️ "+_t("ลบ","Delete"),
                     key="vol_do_del", use_container_width=True):
            if sel_id: st.session_state["vol_pending_del"] = sel_id; st.rerun()

        if st.session_state.get("vol_pending_del") == sel_id and sel_id:
            st.warning(_t(f"⚠️ ยืนยันลบ '{sel_lbl}'?",f"⚠️ Confirm delete '{sel_lbl}'?"))
            cy,cn = st.columns(2)
            if cy.button("✅ "+_t("ยืนยัน","Yes, Delete"), key="vol_del_yes"):
                with get_sync_db() as db:
                    obj = db.get(Volunteer, sel_id)
                    if obj: db.delete(obj)
                st.session_state.pop("vol_pending_del", None)
                st.success(_t("ลบสำเร็จ","Deleted.")); st.rerun()
            if cn.button("❌ "+_t("ยกเลิก","Cancel"), key="vol_del_no"):
                st.session_state.pop("vol_pending_del", None); st.rerun()

    # ── Add button at bottom ──────────────────────────────────────────────────
    st.divider()
    if st.button("➕ "+_t("เพิ่มอาสาสมัครใหม่","Add New Volunteer"),
                 key="vol_add_btn", type="primary", use_container_width=True):
        st.session_state["vol_mode"] = "add"; st.rerun()


def _vol_form(form_key, rec):
    actor  = get_current_user().email if get_current_user() else "system"
    is_th  = st.session_state.get("lang","TH") == "TH"
    vsl    = volunteer_status_labels()
    status_opts = [e.value for e in VolunteerStatus]
    POSITIONS = [
        "อสม.ประจำหมู่บ้าน","อสม.ผู้นำชุมชน","อสม.ชำนาญการ",
        "อสม.ดีเด่น","อสม.ดูแลผู้สูงอายุ","อสม.อาวุโส"
    ] if is_th else [
        "Village Health Volunteer","Community Leader VHV","Specialist VHV",
        "Outstanding VHV","Elderly Care VHV","Senior VHV"
    ]

    with st.form(form_key):
        st.markdown("##### " + _t("ข้อมูลหลัก","Basic Info"))
        c1,c2 = st.columns(2)
        code = c1.text_input(_t("รหัส อสม.","Volunteer Code"),
                              value=rec.volunteer_code if rec else "")
        name = c2.text_input(_t("ชื่อ-นามสกุล *","Full Name *"),
                              value=rec.full_name if rec else "")
        c3,c4 = st.columns(2)
        phone = c3.text_input(_t("โทรศัพท์","Phone"),
                               value=rec.phone or "" if rec else "")
        email = c4.text_input("Email",
                               value=getattr(rec,"email","") or "" if rec else "")
        c5,c6 = st.columns(2)
        pos_val = rec.position if rec and rec.position else POSITIONS[0]
        pos_idx = POSITIONS.index(pos_val) if pos_val in POSITIONS else 0
        position = c5.selectbox(_t("ตำแหน่ง","Position"), POSITIONS, index=pos_idx)
        cur_s    = rec.status if rec and rec.status in status_opts else status_opts[0]
        status   = c6.selectbox(_t("สถานะ","Status"), status_opts,
                                 index=status_opts.index(cur_s),
                                 format_func=lambda x: vsl.get(x,x))

        st.markdown("##### " + _t("ที่อยู่","Location"))
        l1,l2,l3 = st.columns(3)
        province    = l1.text_input(_t("จังหวัด","Province"),
                                     value=rec.province or "" if rec else "")
        district    = l2.text_input(_t("อำเภอ","District"),
                                     value=rec.district or "" if rec else "")
        subdistrict = l3.text_input(_t("ตำบล","Subdistrict"),
                                     value=rec.subdistrict or "" if rec else "")
        village     = st.text_input(_t("หมู่บ้าน","Village"),
                                     value=rec.village or "" if rec else "")

        sub = st.form_submit_button(_t("💾 บันทึก","💾 Save"),
                                     type="primary", use_container_width=True)

    if sub and code and name:
        with get_sync_db() as db:
            if rec:
                obj = db.get(Volunteer, str(rec.id))
                if obj:
                    obj.volunteer_code=code; obj.full_name=name
                    obj.phone=phone or None; obj.email=email or None
                    obj.position=position; obj.province=province or None
                    obj.district=district or None; obj.subdistrict=subdistrict or None
                    obj.village=village or None; obj.status=status
                    obj.updated_by=actor
                st.success(_t("แก้ไขสำเร็จ","Updated."))
            else:
                db.add(Volunteer(
                    volunteer_code=code, full_name=name, phone=phone or None,
                    email=email or None, position=position, province=province or None,
                    district=district or None, subdistrict=subdistrict or None,
                    village=village or None, status=status,
                    created_by=actor, updated_by=actor
                ))
                st.success(_t("เพิ่มอาสาสมัครสำเร็จ","Volunteer added."))
        set_list("vol"); st.rerun()
    elif sub:
        st.warning(_t("กรุณากรอกรหัสและชื่อ","Code and name are required."))
