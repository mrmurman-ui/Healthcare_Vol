"""Referrals — Add / Edit / Delete with full Thai/EN bilingual."""
from datetime import date
import streamlit as st
from sqlalchemy import select
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.localization.service import t
from app.modules.referrals.model import Referral
from app.shared.crud_utils import init_crud_state, crud_toolbar, set_edit, set_list
from app.shared.date_utils import fmt_date, be_date_input
from app.shared.enum_labels import referral_status_labels, referral_target_labels
from app.shared.enums import ReferralStatus, ReferralTarget
HOSPITALS = ["โรงพยาบาลมหาราชนครเชียงใหม่","โรงพยาบาลนครพิงค์","โรงพยาบาลเชียงใหม่ราม","โรงพยาบาลลานนา","โรงพยาบาลแมคคอร์มิค","โรงพยาบาลสันทราย","โรงพยาบาลหางดง","โรงพยาบาลดอยสะเก็ด","โรงพยาบาลลำพูน"]
HEALTH_CENTERS = ["รพ.สต.บ้านสันทรายหลวง","รพ.สต.บ้านหนองหอย","รพ.สต.วัดเกต","รพ.สต.บ้านป่าแดด","ศูนย์สุขภาพชุมชนช้างเผือก","ศูนย์บริการสาธารณสุข 1 (หายยา)","คลินิกชุมชนอบอุ่น สันทราย"]
MUNICIPALITIES = ["เทศบาลนครเชียงใหม่","เทศบาลเมืองแม่เหียะ","เทศบาลตำบลสันทรายหลวง","ศูนย์อนามัยเขตที่ 1 เชียงใหม่","สำนักงานสาธารณสุขอำเภอเมืองเชียงใหม่"]
NGOS = ["มูลนิธิปอเต็กตึ้ง","มูลนิธิกระจกเงา","มูลนิธิสายไหมต้องรอด","มูลนิธิศุภนิมิตแห่งประเทศไทย","สภากาชาดไทย สาขาเชียงใหม่"]

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en

STATUS_TH = {"pending":"รอดำเนินการ","in_progress":"กำลังดำเนินการ","completed":"เสร็จสิ้น","cancelled":"ยกเลิก"}
TARGET_TH = {"hospital":"โรงพยาบาล","health_center":"รพ.สต./ศูนย์สุขภาพ","municipality":"เทศบาล/อปท.","ngo":"มูลนิธิ/NGO"}


def render_referrals() -> None:
    st.header(t("nav_referrals"))

    # Profile navigation
    if st.session_state.get("cit_profile_id"):
        from app.modules.citizens.profile import render_citizen_profile
        render_citizen_profile(st.session_state["cit_profile_id"])
        return

    init_crud_state("ref")
    mode = crud_toolbar("ref","การส่งต่อ","Referral")

    if mode == "add":
        st.subheader("➕ " + _t("สร้างการส่งต่อใหม่","Create Referral"))
        _ref_form("ref_add", None); return

    if mode == "edit":
        eid = st.session_state.get("ref_edit_id")
        with get_sync_db() as db: rec = db.get(Referral, eid)
        if rec:
            st.subheader("✏️ " + _t("แก้ไขการส่งต่อ","Edit Referral"))
            _ref_form("ref_edit", rec)
        else:
            st.error(_t("ไม่พบข้อมูล","Not found"))
        return

    f1,f2,f3 = st.columns(3)
    is_th = st.session_state.get("lang","TH")=="TH"
    status_opts = [""]+[e.value for e in ReferralStatus]
    f_status = f1.selectbox(_t("สถานะ","Status"), status_opts, format_func=lambda x: STATUS_TH.get(x,"ทั้งหมด" if not x else x) if is_th else (x or "All"))
    target_opts = [""]+[e.value for e in ReferralTarget]
    f_target = f2.selectbox(_t("จุดหมาย","Target"), target_opts, format_func=lambda x: TARGET_TH.get(x,"ทั้งหมด" if not x else x) if is_th else (x or "All"))
    f_search = f3.text_input("🔍 " + _t("ค้นหา","Search"))

    with get_sync_db() as db:
        stmt = select(Referral)
        if f_status: stmt = stmt.where(Referral.status == f_status)
        if f_target: stmt = stmt.where(Referral.target == f_target)
        refs = db.execute(stmt.order_by(Referral.referral_date.desc())).scalars().all()

    if refs:
        STATUS_ICON = {"pending":"🟡","in_progress":"🔵","completed":"🟢","cancelled":"⚫"}
        # Load citizen names for all referrals
        from sqlalchemy import text as _text_r
        ref_cit_ids = [str(r.citizen_id) for r in refs if r.citizen_id]
        cit_name_map = {}
        if ref_cit_ids:
            with get_sync_db() as _db:
                crows = _db.execute(_text_r(
                    "SELECT id::text, full_name FROM citizens WHERE id::text = ANY(:ids)"
                ), {"ids": ref_cit_ids}).fetchall()
                cit_name_map = {str(r[0]): r[1] for r in crows}

        for r in refs:
            s_lbl = STATUS_TH.get(r.status,r.status) if is_th else r.status
            t_lbl = TARGET_TH.get(r.target,r.target) if is_th else r.target
            cit_name = cit_name_map.get(str(r.citizen_id),"—") if r.citizen_id else "—"
            c0,c1,c2,c3,cp,ce,cd = st.columns([2,3,2,2,1,1,1])
            c0.markdown(f"**{cit_name}**")
            c1.markdown(f"{STATUS_ICON.get(r.status,'⚪')} **{r.target_name or t_lbl}**  \n{(r.reason or '')[:40]}")
            c2.markdown(f"{t_lbl}  \n{fmt_date(r.referral_date)}")
            c3.markdown(s_lbl)
            if r.citizen_id and cp.button("👤",key=f"rp_{r.id}",help=_t("ดูโปรไฟล์","Profile")):
                st.session_state["cit_profile_id"] = str(r.citizen_id); st.rerun()
            if ce.button("✏️",key=f"re_{r.id}",help=_t("แก้ไข","Edit")): set_edit("ref",r.id)
            if cd.button("🗑️",key=f"rd_{r.id}",help=_t("ลบ","Delete")):
                st.session_state[f"ref_del_{r.id}"] = True; st.rerun()
            if st.session_state.get(f"ref_del_{r.id}"):
                st.warning(_t("ยืนยันลบการส่งต่อนี้?","Confirm delete this referral?"))
                y,n = st.columns(2)
                if y.button("✅",key=f"rdy_{r.id}"):
                    with get_sync_db() as db:
                        obj = db.get(Referral,str(r.id))
                        if obj: db.delete(obj)
                    del st.session_state[f"ref_del_{r.id}"]
                    st.success(_t("ลบแล้ว","Deleted.")); st.rerun()
                if n.button("❌",key=f"rdn_{r.id}"):
                    del st.session_state[f"ref_del_{r.id}"]; st.rerun()
            st.divider()
        st.caption(_t(f"ทั้งหมด {len(refs)} รายการ",f"Total: {len(refs)} referrals"))
    else:
        st.info(_t("ยังไม่มีการส่งต่อ","No referrals found."))


def _ref_form(form_key, rec):
    actor = get_current_user().email if get_current_user() else "system"
    is_th = st.session_state.get("lang","TH")=="TH"
    with get_sync_db() as db:
        cits = db.execute(select(Citizen).order_by(Citizen.full_name).limit(300)).scalars().all()
    cit_opts = {_t("— ไม่เชื่อมโยง —","— None —"): None}
    cit_opts.update({f"{c.full_name}": str(c.id) for c in cits})
    target_vals = [e.value for e in ReferralTarget]
    status_vals = [e.value for e in ReferralStatus]
    TARGET_NAMES = {"hospital": HOSPITALS, "health_center": HEALTH_CENTERS, "municipality": MUNICIPALITIES, "ngo": NGOS}

    with st.form(form_key):
        cit_list = list(cit_opts.keys())
        cur_cit = _t("— ไม่เชื่อมโยง —","— None —")
        if rec and rec.citizen_id:
            match = [k for k,v in cit_opts.items() if v == str(rec.citizen_id)]
            if match: cur_cit = match[0]
        cit_sel = st.selectbox(_t("ประชาชน (ไม่บังคับ)","Citizen (optional)"), cit_list,
                               index=cit_list.index(cur_cit) if cur_cit in cit_list else 0)

        c1,c2 = st.columns(2)
        cur_tgt = rec.target if rec and rec.target in target_vals else target_vals[0]
        target_val = c1.selectbox(_t("จุดหมาย","Referral Target"), target_vals,
                                  index=target_vals.index(cur_tgt),
                                  format_func=lambda x: TARGET_TH.get(x,x) if is_th else x)
        # Dynamic name list based on target
        name_opts = TARGET_NAMES.get(target_val, [])
        cur_name = rec.target_name if rec and rec.target_name else (name_opts[0] if name_opts else "")
        if name_opts:
            sel_name = c2.selectbox(_t("ชื่อสถานที่/หน่วยงาน","Facility Name"), name_opts,
                                    index=name_opts.index(cur_name) if cur_name in name_opts else 0)
        else:
            sel_name = c2.text_input(_t("ชื่อสถานที่/หน่วยงาน","Facility Name"), value=cur_name)

        ref_date = be_date_input(_t("วันที่ส่งต่อ","Referral Date"),
                                  value=rec.referral_date if rec and rec.referral_date else date.today(),
                                  key=form_key+"_dt")
        reason = st.text_area(_t("เหตุผลการส่งต่อ","Reason for Referral"), value=rec.reason or "" if rec else "")
        cur_stat = rec.status if rec and rec.status in status_vals else status_vals[0]
        status_val = st.selectbox(_t("สถานะ","Status"), status_vals,
                                  index=status_vals.index(cur_stat),
                                  format_func=lambda x: STATUS_TH.get(x,x) if is_th else x)
        outcome = st.text_area(_t("ผลลัพธ์","Outcome"), value=rec.outcome or "" if rec else "")
        sub = st.form_submit_button(_t("💾 บันทึก","💾 Save"), type="primary", use_container_width=True)

    if sub:
        cit_id = cit_opts.get(cit_sel)
        with get_sync_db() as db:
            if rec:
                obj = db.get(Referral, str(rec.id))
                if obj:
                    obj.citizen_id=cit_id; obj.target=target_val; obj.target_name=sel_name
                    obj.referral_date=ref_date; obj.reason=reason or None
                    obj.status=status_val; obj.outcome=outcome or None; obj.updated_by=actor
                st.success(_t("แก้ไขสำเร็จ","Updated."))
            else:
                db.add(Referral(citizen_id=cit_id,target=target_val,target_name=sel_name,
                                referral_date=ref_date,reason=reason or None,
                                status=status_val,outcome=outcome or None,
                                created_by=actor,updated_by=actor))
                st.success(_t("สร้างการส่งต่อสำเร็จ","Referral created."))
        set_list("ref"); st.rerun()
