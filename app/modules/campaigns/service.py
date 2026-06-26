"""Health Campaigns — Add / Edit / Delete with full Thai/EN bilingual."""
from __future__ import annotations
from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import func, select, text
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.campaigns.model import Campaign
from app.modules.localization.service import t
from app.shared.crud_utils import init_crud_state, crud_toolbar, set_edit, set_list
from app.shared.date_utils import fmt_date, be_date_input, be_date_input_col

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en

CAMPAIGN_TYPES = ["health_screening","vaccination","health_education","disease_prevention","elderly_care","maternal_health","dental_health","mental_health","nutrition","exercise"]
CAMPAIGN_TYPES_TH = {"health_screening":"ตรวจสุขภาพ","vaccination":"ฉีดวัคซีน","health_education":"ให้ความรู้สุขภาพ","disease_prevention":"ป้องกันโรค","elderly_care":"ดูแลผู้สูงอายุ","maternal_health":"อนามัยแม่และเด็ก","dental_health":"ทันตสุขภาพ","mental_health":"สุขภาพจิต","nutrition":"โภชนาการ","exercise":"ออกกำลังกาย"}
CAMPAIGN_STATUSES = ["planning","active","completed","cancelled"]
CAMPAIGN_STATUS_TH = {"planning":"วางแผน","active":"กำลังดำเนินการ","completed":"เสร็จสิ้น","cancelled":"ยกเลิก"}
STATUS_COLORS = {"planning":"#3B82F6","active":"#22C55E","completed":"#8B5CF6","cancelled":"#9CA3AF"}
TARGET_GROUPS = ["all","elderly","children","pregnant","disabled","chronic_disease","women","men","youth"]
TARGET_GROUPS_TH = {"all":"ทุกกลุ่ม","elderly":"ผู้สูงอายุ","children":"เด็ก","pregnant":"หญิงตั้งครรภ์","disabled":"ผู้พิการ","chronic_disease":"ผู้ป่วยโรคเรื้อรัง","women":"ผู้หญิง","men":"ผู้ชาย","youth":"เยาวชน"}


def _ensure_table():
    with get_sync_db() as db:
        db.execute(text("""CREATE TABLE IF NOT EXISTS health_campaigns (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(), campaign_code VARCHAR(50) UNIQUE NOT NULL,
            campaign_name VARCHAR(300) NOT NULL, campaign_type VARCHAR(50) DEFAULT 'health_screening',
            description TEXT, target_group VARCHAR(100), start_date VARCHAR(20), end_date VARCHAR(20),
            province VARCHAR(100), district VARCHAR(100), venue VARCHAR(300), budget FLOAT,
            target_count INTEGER, actual_count INTEGER, status VARCHAR(20) DEFAULT 'planning',
            organizer VARCHAR(200), notes TEXT, is_deleted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW(),
            created_by VARCHAR(100), updated_by VARCHAR(100))"""))


def render_campaigns() -> None:
    _ensure_table()
    st.header("📣 " + _t("แคมเปญสุขภาพ","Health Campaigns"))
    init_crud_state("camp")
    mode = crud_toolbar("camp","แคมเปญ","Campaign")
    is_th = st.session_state.get("lang","TH")=="TH"

    if mode == "add":
        st.subheader("➕ " + _t("เพิ่มแคมเปญ","Add Campaign"))
        _camp_form("camp_add", None); return

    if mode == "edit":
        eid = st.session_state.get("camp_edit_id")
        with get_sync_db() as db: rec = db.get(Campaign, eid)
        if rec:
            st.subheader("✏️ " + _t(f"แก้ไข: {rec.campaign_name}",f"Edit: {rec.campaign_name}"))
            _camp_form("camp_edit", rec)
        else:
            st.error(_t("ไม่พบข้อมูล","Not found"))
        return

    with get_sync_db() as db:
        camps = db.execute(select(Campaign).where(Campaign.is_deleted==False).order_by(Campaign.start_date.desc())).scalars().all()

    # Metrics
    total=len(camps); active=sum(1 for c in camps if c.status=="active")
    completed=sum(1 for c in camps if c.status=="completed")
    t_target=sum(c.target_count or 0 for c in camps); t_actual=sum(c.actual_count or 0 for c in camps)
    reach=round(t_actual/max(t_target,1)*100,1)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric(_t("ทั้งหมด","Total"),total); c2.metric("🟢 "+_t("ดำเนินการ","Active"),active)
    c3.metric("✅ "+_t("เสร็จสิ้น","Done"),completed); c4.metric(_t("เป้าหมายรวม","Target"),f"{t_target:,}")
    c5.metric(_t("ครอบคลุม","Reach"),f"{reach}%")
    st.divider()

    f1,f2,f3 = st.columns(3)
    f_stat = f1.selectbox(_t("สถานะ","Status"),[""]+CAMPAIGN_STATUSES,
                          format_func=lambda x: CAMPAIGN_STATUS_TH.get(x,"ทั้งหมด") if is_th and x else ("All" if not x else x))
    f_type = f2.selectbox(_t("ประเภท","Type"),[""]+CAMPAIGN_TYPES,
                          format_func=lambda x: CAMPAIGN_TYPES_TH.get(x,"ทั้งหมด") if is_th and x else ("All" if not x else x))
    f_q    = f3.text_input("🔍 "+_t("ค้นหา","Search"))
    filtered = [c for c in camps
                if (not f_stat or c.status==f_stat)
                and (not f_type or c.campaign_type==f_type)
                and (not f_q or f_q.lower() in (c.campaign_name or "").lower())]

    if filtered:
        for camp in filtered:
            s_lbl = CAMPAIGN_STATUS_TH.get(camp.status,camp.status) if is_th else camp.status
            t_lbl = CAMPAIGN_TYPES_TH.get(camp.campaign_type,camp.campaign_type or "") if is_th else (camp.campaign_type or "")
            tgt = camp.target_count or 0; act = camp.actual_count or 0
            pct = round(act/max(tgt,1)*100,1)
            c1,c2,c3,ce,cd = st.columns([4,2,2,1,1])
            c1.markdown(f"**{camp.campaign_name}**  \n`{camp.campaign_code}` · {t_lbl}")
            c2.markdown(f"{s_lbl}  \n{fmt_date(camp.start_date)}")
            c3.markdown(f"🎯 {act:,}/{tgt:,} ({pct}%)")
            if ce.button("✏️",key=f"campe_{camp.id}",help=_t("แก้ไข","Edit")): set_edit("camp",camp.id)
            if cd.button("🗑️",key=f"campd_{camp.id}",help=_t("ลบ","Delete")):
                st.session_state[f"camp_del_{camp.id}"]=True; st.rerun()
            if st.session_state.get(f"camp_del_{camp.id}"):
                st.warning(_t(f"ยืนยันลบ '{camp.campaign_name}'?",f"Delete '{camp.campaign_name}'?"))
                y,n=st.columns(2)
                if y.button("✅",key=f"campdy_{camp.id}"):
                    with get_sync_db() as db:
                        obj=db.get(Campaign,str(camp.id))
                        if obj: obj.is_deleted=True
                    del st.session_state[f"camp_del_{camp.id}"]
                    st.success(_t("ลบแล้ว","Deleted.")); st.rerun()
                if n.button("❌",key=f"campdn_{camp.id}"):
                    del st.session_state[f"camp_del_{camp.id}"]; st.rerun()
            st.divider()
        st.caption(_t(f"แสดง {len(filtered)}/{total} แคมเปญ",f"Showing {len(filtered)}/{total}"))
    else:
        st.info(_t("ยังไม่มีแคมเปญ","No campaigns found."))


def _camp_form(form_key, rec):
    actor = get_current_user().email if get_current_user() else "system"
    is_th = st.session_state.get("lang","TH")=="TH"
    with st.form(form_key):
        c1,c2,c3 = st.columns(3)
        code = c1.text_input(_t("รหัสแคมเปญ","Code"), value=rec.campaign_code if rec else "")
        name = c2.text_input(_t("ชื่อแคมเปญ","Name"), value=rec.campaign_name if rec else "")
        cur_type = rec.campaign_type if rec and rec.campaign_type in CAMPAIGN_TYPES else CAMPAIGN_TYPES[0]
        ctype = c3.selectbox(_t("ประเภท","Type"),CAMPAIGN_TYPES,index=CAMPAIGN_TYPES.index(cur_type),
                             format_func=lambda x: CAMPAIGN_TYPES_TH.get(x,x) if is_th else x)
        c4,c5,c6 = st.columns(3)
        cur_tg = rec.target_group if rec and rec.target_group in TARGET_GROUPS else TARGET_GROUPS[0]
        tg = c4.selectbox(_t("กลุ่มเป้าหมาย","Target Group"),TARGET_GROUPS,index=TARGET_GROUPS.index(cur_tg),
                          format_func=lambda x: TARGET_GROUPS_TH.get(x,x) if is_th else x)
        cur_stat = rec.status if rec and rec.status in CAMPAIGN_STATUSES else CAMPAIGN_STATUSES[0]
        status = c5.selectbox(_t("สถานะ","Status"),CAMPAIGN_STATUSES,index=CAMPAIGN_STATUSES.index(cur_stat),
                              format_func=lambda x: CAMPAIGN_STATUS_TH.get(x,x) if is_th else x)
        organizer = c6.text_input(_t("ผู้จัดงาน","Organizer"), value=rec.organizer or "" if rec else "")
        c7,c8 = st.columns(2)
        start = be_date_input_col(c7,_t("วันที่เริ่ม","Start Date"),value=date.today(),key=form_key+"_s")
        end   = be_date_input_col(c8,_t("วันที่สิ้นสุด","End Date"),value=date.today(),key=form_key+"_e")
        c9,c10,c11 = st.columns(3)
        target_cnt = c9.number_input(_t("เป้าหมาย","Target Count"),value=int(rec.target_count or 0) if rec else 0,min_value=0)
        actual_cnt = c10.number_input(_t("ผู้เข้าร่วมจริง","Actual Count"),value=int(rec.actual_count or 0) if rec else 0,min_value=0)
        budget = c11.number_input(_t("งบประมาณ (บาท)","Budget"),value=float(rec.budget or 0) if rec else 0.0,min_value=0.0)
        venue = st.text_input(_t("สถานที่","Venue"),value=rec.venue or "" if rec else "")
        c12,c13 = st.columns(2)
        province = c12.text_input(_t("จังหวัด","Province"),value=rec.province or "" if rec else "")
        district = c13.text_input(_t("อำเภอ","District"),value=rec.district or "" if rec else "")
        desc  = st.text_area(_t("รายละเอียด","Description"),value=rec.description or "" if rec else "")
        notes = st.text_area(_t("หมายเหตุ","Notes"),value=rec.notes or "" if rec else "")
        sub = st.form_submit_button(_t("💾 บันทึก","💾 Save"),type="primary",use_container_width=True)
    if sub and code and name:
        with get_sync_db() as db:
            if rec:
                obj=db.get(Campaign,str(rec.id))
                if obj:
                    obj.campaign_code=code; obj.campaign_name=name; obj.campaign_type=ctype
                    obj.target_group=tg; obj.status=status; obj.organizer=organizer or None
                    obj.start_date=str(start); obj.end_date=str(end)
                    obj.target_count=target_cnt or None; obj.actual_count=actual_cnt or None
                    obj.budget=budget or None; obj.venue=venue or None
                    obj.province=province or None; obj.district=district or None
                    obj.description=desc or None; obj.notes=notes or None
                st.success(_t("แก้ไขสำเร็จ","Updated."))
            else:
                db.add(Campaign(campaign_code=code,campaign_name=name,campaign_type=ctype,
                                target_group=tg,status=status,organizer=organizer or None,
                                start_date=str(start),end_date=str(end),
                                target_count=target_cnt or None,actual_count=actual_cnt or None,
                                budget=budget or None,venue=venue or None,
                                province=province or None,district=district or None,
                                description=desc or None,notes=notes or None,
                                created_by=actor,updated_by=actor))
                st.success(_t("เพิ่มแคมเปญสำเร็จ","Campaign added."))
        set_list("camp"); st.rerun()
    elif sub:
        st.warning(_t("กรุณากรอกรหัสและชื่อแคมเปญ","Code and name required."))
