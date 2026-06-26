"""Households — Add / Edit / Delete + Profile view with family members."""
import streamlit as st
from sqlalchemy import select
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.households.model import Household
from app.modules.households.profile import render_household_profile
from app.modules.localization.service import t
from app.shared.crud_utils import init_crud_state, crud_toolbar, set_edit, set_list
from app.shared.enums import HousingType, IncomeGroup

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en

INCOME_TH  = {"very_low":"รายได้น้อยมาก","low":"รายได้น้อย","medium":"รายได้ปานกลาง","high":"รายได้สูง"}
HOUSING_TH = {"own":"บ้านตัวเอง","rent":"เช่า","free":"อาศัยฟรี","other":"อื่นๆ"}


def render_households() -> None:
    st.header(t("nav_households"))

    # ── Profile view ──────────────────────────────────────────────────────────
    if st.session_state.get("hh_profile_id"):
        render_household_profile(st.session_state["hh_profile_id"])
        return

    init_crud_state("hh")
    mode = crud_toolbar("hh","ครัวเรือน","Household")

    if mode == "add":
        st.subheader("➕ " + _t("เพิ่มครัวเรือน","Add Household"))
        _hh_form("hh_add", None); return

    if mode == "edit":
        eid = st.session_state.get("hh_edit_id")
        with get_sync_db() as db: rec = db.get(Household, eid)
        if rec:
            st.subheader("✏️ " + _t(f"แก้ไข: {rec.household_code}",f"Edit: {rec.household_code}"))
            _hh_form("hh_edit", rec)
        else:
            st.error(_t("ไม่พบข้อมูล","Not found"))
        return

    # ── List ──────────────────────────────────────────────────────────────────
    f1, f2 = st.columns([3,1])
    query = f1.text_input("🔍 " + t("search"), key="hh_search")
    is_th = st.session_state.get("lang","TH")=="TH"

    with get_sync_db() as db:
        stmt = select(Household)
        if query:
            stmt = stmt.where(
                Household.household_code.ilike(f"%{query}%") |
                Household.head_of_household.ilike(f"%{query}%")
            )
        hhs = db.execute(stmt.order_by(Household.household_code)).scalars().all()

    if hhs:
        # Header
        h1,h2,h3,h4,h5,h6 = st.columns([2,2,2,1,1,1])
        for col,lbl in zip([h1,h2,h3,h4,h5,h6],[
            _t("รหัส/หัวหน้า","Code/Head"),
            _t("ที่อยู่","Location"),
            _t("รายได้","Income"),
            "👁️","✏️","🗑️"
        ]):
            col.markdown(f"**{lbl}**")
        st.divider()

        for h in hhs:
            inc = INCOME_TH.get(h.income_group or "","") if is_th else (h.income_group or "")
            c1,c2,c3,cv,ce,cd = st.columns([2,2,2,1,1,1])
            c1.markdown(f"**{h.household_code}**  \n{h.head_of_household or '—'}")
            c2.markdown(f"{h.village or ''} {h.district or ''}")
            c3.markdown(inc or "—")

            if cv.button("👁️",key=f"hhv_{h.id}",help=_t("ดูโปรไฟล์","View Profile")):
                st.session_state["hh_profile_id"] = str(h.id); st.rerun()
            if ce.button("✏️",key=f"hhe_{h.id}",help=_t("แก้ไข","Edit")):
                set_edit("hh",h.id)
            if cd.button("🗑️",key=f"hhd_{h.id}",help=_t("ลบ","Delete")):
                st.session_state[f"hh_del_{h.id}"] = True; st.rerun()

            if st.session_state.get(f"hh_del_{h.id}"):
                st.warning(_t(f"ยืนยันลบครัวเรือน '{h.household_code}'?",
                               f"Delete '{h.household_code}'?"))
                y,n = st.columns(2)
                if y.button("✅",key=f"hhdy_{h.id}"):
                    with get_sync_db() as db:
                        obj = db.get(Household,str(h.id))
                        if obj: db.delete(obj)
                    del st.session_state[f"hh_del_{h.id}"]
                    st.success(_t("ลบแล้ว","Deleted.")); st.rerun()
                if n.button("❌",key=f"hhdn_{h.id}"):
                    del st.session_state[f"hh_del_{h.id}"]; st.rerun()
            st.divider()
        st.caption(_t(f"ทั้งหมด {len(hhs)} ครัวเรือน",f"Total: {len(hhs)} households"))
    else:
        st.info(_t("ยังไม่มีข้อมูลครัวเรือน","No households found."))


def _hh_form(form_key, rec):
    actor = get_current_user().email if get_current_user() else "system"
    is_th = st.session_state.get("lang","TH")=="TH"
    income_opts  = list(INCOME_TH.keys())
    housing_opts = list(HOUSING_TH.keys())
    def il(v): return INCOME_TH.get(v,v) if is_th else v
    def hl(v): return HOUSING_TH.get(v,v) if is_th else v

    with st.form(form_key):
        c1,c2 = st.columns(2)
        code = c1.text_input(_t("รหัสครัวเรือน","Household Code"),
                              value=rec.household_code if rec else "")
        head = c2.text_input(_t("หัวหน้าครัวเรือน","Head of Household"),
                              value=rec.head_of_household or "" if rec else "")
        addr = st.text_area(_t("ที่อยู่","Address"),
                             value=rec.address or "" if rec else "")
        c3,c4,c5 = st.columns(3)
        village  = c3.text_input(_t("หมู่บ้าน/ชุมชน","Village"),
                                   value=rec.village or "" if rec else "")
        district = c4.text_input(_t("อำเภอ","District"),
                                   value=rec.district or "" if rec else "")
        province = c5.text_input(_t("จังหวัด","Province"),
                                   value=rec.province or "" if rec else "")
        c6,c7 = st.columns(2)
        phone    = c6.text_input(_t("โทรศัพท์","Phone"),
                                   value=rec.phone or "" if rec else "")
        community= c7.text_input(_t("ชุมชน","Community"),
                                   value=rec.community or "" if rec and hasattr(rec,"community") else "")
        c8,c9 = st.columns(2)
        cur_inc = rec.income_group  if rec and rec.income_group  in income_opts  else income_opts[1]
        cur_hou = rec.housing_type  if rec and rec.housing_type  in housing_opts else housing_opts[0]
        inc = c8.selectbox(_t("กลุ่มรายได้","Income Group"), income_opts,
                           index=income_opts.index(cur_inc), format_func=il)
        hou = c9.selectbox(_t("ประเภทที่อยู่","Housing Type"), housing_opts,
                           index=housing_opts.index(cur_hou), format_func=hl)
        c10,c11 = st.columns(2)
        lat = c10.number_input("GPS Latitude",  value=float(rec.latitude  or 0) if rec else 0.0, format="%.6f")
        lon = c11.number_input("GPS Longitude", value=float(rec.longitude or 0) if rec else 0.0, format="%.6f")
        sub = st.form_submit_button(_t("💾 บันทึก","💾 Save"), type="primary", use_container_width=True)

    if sub and code:
        with get_sync_db() as db:
            if rec:
                obj = db.get(Household,str(rec.id))
                if obj:
                    obj.household_code=code; obj.head_of_household=head or None
                    obj.address=addr or None; obj.village=village or None
                    obj.district=district or None; obj.province=province or None
                    obj.phone=phone or None; obj.income_group=inc; obj.housing_type=hou
                    obj.latitude=lat or None; obj.longitude=lon or None
                    obj.updated_by=actor
                st.success(_t("แก้ไขสำเร็จ","Updated."))
            else:
                db.add(Household(household_code=code,head_of_household=head or None,
                                 address=addr or None,village=village or None,
                                 district=district or None,province=province or None,
                                 phone=phone or None,income_group=inc,housing_type=hou,
                                 latitude=lat or None,longitude=lon or None,
                                 created_by=actor,updated_by=actor))
                st.success(_t("เพิ่มครัวเรือนสำเร็จ","Household added."))
        set_list("hh"); st.rerun()
    elif sub:
        st.warning(_t("กรุณากรอกรหัสครัวเรือน","Household code is required."))
