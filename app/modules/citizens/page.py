"""Citizens — Multi-filter · Elderly sub-view · Running ID · Thai headers · No-freeze."""
from __future__ import annotations
from datetime import date
import pandas as pd
import streamlit as st
from sqlalchemy import select, text, func
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.localization.service import t
from app.modules.citizens.profile import render_citizen_profile
from app.shared.crud_utils import init_crud_state, set_edit, set_list
from app.shared.date_utils import fmt_date, be_date_input, ad_to_be_year
from app.shared.enum_labels import gender_labels
from app.shared.enums import Gender

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en
def _is_th():   return st.session_state.get("lang","TH")=="TH"

PAGE_SIZE = 50


# ── Ensure extra DB columns ───────────────────────────────────────────────────
def _ensure_columns():
    # ── Context 1: Add columns (ALTER TABLE — each in own try) ───────────────
    for col, coltype in [
        ("citizen_code","VARCHAR(20)"),
        ("community_code","VARCHAR(10)"),
        ("house_number","VARCHAR(50)"),
        ("village","VARCHAR(100)"),
        ("district","VARCHAR(100)"),
        ("address","TEXT"),
        ("notes","TEXT"),
        ("is_deleted","BOOLEAN DEFAULT FALSE"),
        ("national_id","VARCHAR(13)"),
    ]:
        try:
            with get_sync_db() as _db:
                _db.execute(text(
                    f"ALTER TABLE citizens ADD COLUMN IF NOT EXISTS {col} {coltype}"
                ))
        except Exception:
            pass

    # ── Context 2: Assign CA codes (separate commit) ──────────────────────────
    try:
        with get_sync_db() as db2:
            max_row = db2.execute(text(
                "SELECT citizen_code FROM citizens "
                "WHERE citizen_code LIKE 'CA%' "
                "ORDER BY citizen_code DESC LIMIT 1"
            )).fetchone()
            start = 1
            if max_row and max_row[0]:
                try: start = int(max_row[0][2:]) + 1
                except: start = 1
            no_code = db2.execute(text(
                "SELECT id FROM citizens "
                "WHERE (citizen_code IS NULL OR citizen_code = '') "
                "ORDER BY created_at, full_name"
            )).fetchall()
            for i, row in enumerate(no_code):
                db2.execute(text(
                    "UPDATE citizens SET citizen_code=:code "
                    "WHERE id=:id AND (citizen_code IS NULL OR citizen_code='')"
                ), {"code": f"CA{start+i:05d}", "id": str(row[0])})
            # Context manager auto-commits here
    except Exception:
        pass


def _calc_age(dob) -> int | None:
    if dob is None: return None
    try:
        from datetime import datetime
        born = dob if hasattr(dob,"year") else datetime.strptime(str(dob)[:10],"%Y-%m-%d").date()
        td = date.today()
        return td.year - born.year - ((td.month,td.day)<(born.month,born.day))
    except: return None


def _next_citizen_code(community_code: str = "A") -> str:
    """Generate running number code like A100001, A100002, …"""
    with get_sync_db() as db:
        result = db.execute(text("""
            SELECT citizen_code FROM citizens
            WHERE citizen_code LIKE :prefix
            ORDER BY citizen_code DESC LIMIT 1
        """), {"prefix": f"{community_code}%"}).fetchone()
    if result and result[0]:
        try:
            num = int(result[0][len(community_code):]) + 1
        except ValueError:
            num = 100001
    else:
        num = 100001
    return f"{community_code}{num:06d}"


# ── Main entry point ──────────────────────────────────────────────────────────
def render_citizens() -> None:
    _ensure_columns()
    st.header(t("nav_citizens"))

    # Profile view override
    if st.session_state.get("cit_profile_id"):
        render_citizen_profile(st.session_state["cit_profile_id"])
        return

    init_crud_state("cit")

    # Mode tabs: ALL / ELDERLY
    tab_all, tab_eld = st.tabs([
        "👥 " + _t("ประชาชนทั้งหมด","All Citizens"),
        "👴 " + _t("ผู้สูงอายุ","Elderly Citizens"),
    ])

    with tab_all:
        _render_list(elderly_only=False)

    with tab_eld:
        _render_elderly()


# ── Shared list renderer ──────────────────────────────────────────────────────
def _render_list(elderly_only: bool = False):
    is_th = _is_th()
    _gl   = gender_labels()
    suffix = "_e" if elderly_only else ""
    mode   = st.session_state.get("cit_mode","list")

    # ── ADD form (moved to BOTTOM — shown via button below table) ────────────
    if mode == "add":
        st.subheader("➕ " + _t("เพิ่มประชาชน","Add Citizen"))
        _citizen_form("cit_add", None)
        if st.button("← " + _t("ย้อนกลับ","Back"), key=f"cit_back{suffix}"):
            set_list("cit")
        return

    if mode == "edit":
        eid = st.session_state.get("cit_edit_id")
        with get_sync_db() as db:
            rec = db.get(Citizen, eid)
        if rec:
            st.subheader("✏️ " + _t(f"แก้ไข: {rec.full_name}",f"Edit: {rec.full_name}"))
            _citizen_form("cit_edit", rec)
        else:
            st.error(_t("ไม่พบข้อมูล","Record not found"))
        if st.button("← " + _t("ย้อนกลับ","Back"), key=f"cit_back_e{suffix}"):
            set_list("cit")
        return

    # ── Search & filter panel ─────────────────────────────────────────────────
    with st.expander("🔍 " + _t("ค้นหาและกรอง","Search & Filter"), expanded=True):
        r1c1,r1c2,r1c3 = st.columns([3,2,2])
        f_name   = r1c1.text_input(_t("ชื่อ-นามสกุล","Full Name"),
                                    key=f"cf_name{suffix}",
                                    placeholder=_t("พิมพ์ชื่อ...","Type name..."))
        g_opts   = [_t("ทุกเพศ","All Genders")] + [_gl.get(e.value,e.value) for e in Gender]
        g_raw    = [None] + [e.value for e in Gender]
        g_idx    = r1c2.selectbox(_t("เพศ","Gender"), range(len(g_opts)),
                                   format_func=lambda i:g_opts[i], key=f"cf_g{suffix}")
        f_gender = g_raw[g_idx]
        f_code   = r1c3.text_input(_t("รหัสประชาชน","Citizen Code"),
                                    key=f"cf_code{suffix}", placeholder="เช่น A100001")

        r2c1,r2c2,r2c3 = st.columns(3)
        f_house    = r2c1.text_input(_t("บ้านเลขที่","House No."), key=f"cf_hn{suffix}")
        f_village  = r2c2.text_input(_t("หมู่บ้าน/ชุมชน","Village"), key=f"cf_vl{suffix}")
        f_district = r2c3.text_input(_t("อำเภอ","District"), key=f"cf_dist{suffix}")

        r3c1,r3c2,r3c3 = st.columns(3)
        f_age_min  = r3c1.number_input(_t("อายุต่ำสุด (ปี)","Min Age"),
                                        0,120,0, key=f"cf_amin{suffix}")
        f_age_max  = r3c2.number_input(_t("อายุสูงสุด (ปี)","Max Age"),
                                        0,120,120, key=f"cf_amax{suffix}")
        f_occ      = r3c3.text_input(_t("อาชีพ","Occupation"), key=f"cf_occ{suffix}")

        # Vulnerability filters
        st.markdown("##### " + _t("กลุ่มเปราะบาง","Vulnerability"))
        vc1,vc2,vc3,vc4,vc5 = st.columns(5)
        f_eld  = vc1.checkbox("👴 "+_t("ผู้สูงอายุ","Elderly"),    key=f"cf_eld{suffix}")
        f_dis  = vc2.checkbox("♿ "+_t("ผู้พิการ","Disabled"),      key=f"cf_dis{suffix}")
        f_bed  = vc3.checkbox("🛏️ "+_t("ติดเตียง","Bedridden"),   key=f"cf_bed{suffix}")
        f_preg = vc4.checkbox("🤰 "+_t("ตั้งครรภ์","Pregnant"),    key=f"cf_preg{suffix}")
        f_aln  = vc5.checkbox("🏠 "+_t("อยู่คนเดียว","Alone"),     key=f"cf_aln{suffix}")

        # Disease filters (for elderly view)
        if elderly_only:
            st.markdown("##### " + _t("โรคเรื้อรัง","Chronic Conditions"))
            dc1,dc2,dc3,dc4 = st.columns(4)
            f_dm   = dc1.checkbox("🩸 "+_t("เบาหวาน","Diabetes"),          key=f"cf_dm{suffix}")
            f_ht   = dc2.checkbox("❤️ "+_t("ความดันโลหิตสูง","Hypertension"), key=f"cf_ht{suffix}")
            f_hd   = dc3.checkbox("💊 "+_t("โรคหัวใจ","Heart Disease"),      key=f"cf_hd{suffix}")
            f_hb   = dc4.checkbox("🏠 "+_t("ติดบ้าน","Homebound"),           key=f"cf_hb{suffix}")
        else:
            f_dm = f_ht = f_hd = f_hb = False

        # Force elderly=True for elderly tab
        if elderly_only:
            f_eld = True

        clr_keys = [f"cf_name{suffix}",f"cf_g{suffix}",f"cf_code{suffix}",
                    f"cf_hn{suffix}",f"cf_vl{suffix}",f"cf_dist{suffix}",
                    f"cf_amin{suffix}",f"cf_amax{suffix}",f"cf_occ{suffix}",
                    f"cf_eld{suffix}",f"cf_dis{suffix}",f"cf_bed{suffix}",
                    f"cf_preg{suffix}",f"cf_aln{suffix}",f"cf_dm{suffix}",
                    f"cf_ht{suffix}",f"cf_hd{suffix}",f"cf_hb{suffix}",
                    f"cit_page{suffix}"]
        if st.button("🔄 "+_t("ล้างตัวกรอง","Clear Filters"), key=f"cf_clr{suffix}"):
            for k in clr_keys:
                st.session_state.pop(k, None)
            st.rerun()

    # ── Query ─────────────────────────────────────────────────────────────────
    with get_sync_db() as db:
        stmt = select(Citizen)
        try: stmt = stmt.where(Citizen.is_deleted == False)
        except: pass
        if f_eld:    stmt = stmt.where(Citizen.is_elderly == True)
        if f_dis:    stmt = stmt.where(Citizen.is_disabled == True)
        if f_bed:    stmt = stmt.where(Citizen.is_bedridden == True)
        if f_preg:   stmt = stmt.where(Citizen.is_pregnant == True)
        if f_aln:    stmt = stmt.where(Citizen.is_living_alone == True)
        if f_name:   stmt = stmt.where(Citizen.full_name.ilike(f"%{f_name}%"))
        if f_gender: stmt = stmt.where(Citizen.gender == f_gender)
        if f_occ:    stmt = stmt.where(Citizen.occupation.ilike(f"%{f_occ}%"))
        citizens = db.execute(stmt.order_by(Citizen.full_name)).scalars().all()

    # ── Post-query filters ────────────────────────────────────────────────────
    def _post(c):
        if f_code    and f_code.upper()    not in (getattr(c,"citizen_code","") or "").upper():   return False
        if f_house   and f_house.lower()   not in (getattr(c,"house_number","") or "").lower():   return False
        if f_village and f_village.lower() not in (getattr(c,"village","")      or "").lower():   return False
        if f_district and f_district.lower() not in (getattr(c,"district","")   or "").lower():   return False
        age = _calc_age(c.date_of_birth)
        if age is not None and not (f_age_min <= age <= f_age_max): return False
        return True

    citizens = [c for c in citizens if _post(c)]

    # Disease filters via health_profiles join (post-query for simplicity)
    if any([f_dm, f_ht, f_hd, f_hb]):
        cit_ids = {str(c.id) for c in citizens}
        with get_sync_db() as db:
            rows = db.execute(text("""
                SELECT citizen_id,
                       has_diabetes, has_hypertension, has_heart_disease, is_homebound
                FROM health_profiles
                WHERE citizen_id = ANY(:ids) AND (is_deleted IS NULL OR is_deleted=false)
            """), {"ids": list(cit_ids)}).fetchall()
        prof_map = {str(r[0]): r for r in rows}
        def _disease_ok(c):
            p = prof_map.get(str(c.id))
            if p is None: return False
            if f_dm and not p[1]: return False
            if f_ht and not p[2]: return False
            if f_hd and not p[3]: return False
            if f_hb and not p[4]: return False
            return True
        citizens = [c for c in citizens if _disease_ok(c)]

    total = len(citizens)

    # ── Summary metrics ───────────────────────────────────────────────────────
    s1,s2,s3,s4,s5 = st.columns(5)
    s1.metric(_t("ทั้งหมด","Total"),         total)
    s2.metric("👴 "+_t("ผู้สูงอายุ","Elderly"),   sum(1 for c in citizens if c.is_elderly))
    s3.metric("♿ "+_t("ผู้พิการ","Disabled"),      sum(1 for c in citizens if c.is_disabled))
    s4.metric("🛏️ "+_t("ติดเตียง","Bedridden"),   sum(1 for c in citizens if c.is_bedridden))
    s5.metric("🏠 "+_t("อยู่คนเดียว","Alone"),     sum(1 for c in citizens if c.is_living_alone))

    if total == 0:
        st.info(_t("ไม่พบประชาชนที่ตรงกับเงื่อนไข","No citizens match the filter."))
        # Still show Add button at bottom
        st.divider()
        if st.button("➕ " + _t("เพิ่มประชาชนใหม่","Add New Citizen"),
                     key=f"cit_add_btn_empty{suffix}", type="primary"):
            st.session_state["cit_mode"] = "add"; st.rerun()
        return

    # ── Pagination ────────────────────────────────────────────────────────────
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page_key    = f"cit_page{suffix}"
    page        = max(1, min(st.session_state.get(page_key, 1), total_pages))

    pc1,pc2,pc3 = st.columns([1,4,1])
    if pc1.button("◀ "+_t("ก่อนหน้า","Prev"), disabled=page<=1, key=f"cit_prev{suffix}"):
        st.session_state[page_key] = page - 1; st.rerun()
    pc2.markdown(
        f"<div style='text-align:center;padding-top:6px'>"
        f"{_t('หน้า','Page')} <b>{page}</b> / {total_pages} "
        f"({_t('ทั้งหมด','Total')} {total} {_t('คน','records')})</div>",
        unsafe_allow_html=True
    )
    if pc3.button(_t("ถัดไป","Next")+" ▶", disabled=page>=total_pages, key=f"cit_next{suffix}"):
        st.session_state[page_key] = page + 1; st.rerun()

    # ── Build DataFrame with Thai headers ────────────────────────────────────
    start          = (page - 1) * PAGE_SIZE
    page_citizens  = citizens[start : start + PAGE_SIZE]

    rows = []
    for c in page_citizens:
        age   = _calc_age(c.date_of_birth)
        flags = (("👴" if c.is_elderly    else "") +
                 ("♿" if c.is_disabled   else "") +
                 ("🛏️" if c.is_bedridden  else "") +
                 ("🤰" if c.is_pregnant   else "") +
                 ("🏠" if c.is_living_alone else ""))
        rows.append({
            "id": str(c.id),
            _t("รหัส","Code"):                 getattr(c,"citizen_code","") or "—",
            _t("ชื่อ-นามสกุล","Full Name"):    c.full_name,
            _t("เพศ","Gender"):                _gl.get(c.gender or "", c.gender or "—"),
            _t("อายุ (ปี)","Age (yrs)"):       age if age is not None else "—",
            _t("วันเกิด","DOB"):               fmt_date(c.date_of_birth),
            _t("โทรศัพท์","Phone"):            c.phone or "—",
            _t("อาชีพ","Occupation"):          c.occupation or "—",
            _t("กลุ่มเปราะบาง","Flags"):       flags if flags else "—",
            _t("หมู่บ้าน","Village"):          getattr(c,"village","") or "—",
        })

    df         = pd.DataFrame(rows)
    id_ser     = df["id"]
    display_df = df.drop(columns=["id"])

    st.dataframe(display_df, use_container_width=True, hide_index=True,
                 column_config={
                     _t("อายุ (ปี)","Age (yrs)"): st.column_config.NumberColumn(
                         _t("อายุ (ปี)","Age (yrs)"), format="%d"),
                 })

    st.divider()

    # ── Action panel — single dropdown, no per-row widget loop ───────────────
    st.markdown("#### " + _t("👤 ดูโปรไฟล์ / แก้ไข / ลบ","👤 View Profile / Edit / Delete"))
    st.caption(_t(
        "เลือกชื่อจาก dropdown แล้วกดปุ่ม",
        "Select from dropdown then click action button"
    ))

    sel_opts = {
        f"{getattr(c,'citizen_code','') or '—'}  {c.full_name}": str(c.id)
        for c in page_citizens
    }
    sel_lbl = st.selectbox(
        _t("เลือกประชาชน","Select Citizen"),
        list(sel_opts.keys()), key=f"cit_sel{suffix}"
    )
    sel_id = sel_opts.get(sel_lbl)

    ba1, ba2, ba3 = st.columns(3)
    if ba1.button("👤 " + _t("ดูโปรไฟล์","View Profile"),
                  key=f"cit_prof_btn{suffix}", use_container_width=True, type="primary"):
        if sel_id:
            st.session_state["cit_profile_id"] = sel_id
            st.rerun()
    if ba2.button("✏️ " + _t("แก้ไข","Edit"),
                  key=f"cit_edit_btn{suffix}", use_container_width=True):
        if sel_id: set_edit("cit", sel_id)
    if ba3.button("🗑️ " + _t("ลบ","Delete"),
                  key=f"cit_del_btn{suffix}", use_container_width=True):
        if sel_id:
            st.session_state["cit_pending_del"] = sel_id
            st.rerun()

    if st.session_state.get("cit_pending_del") and        st.session_state["cit_pending_del"] == sel_id:
        st.warning(_t(f"⚠️ ยืนยันลบ '{sel_lbl}'?",f"⚠️ Confirm delete '{sel_lbl}'?"))
        cy, cn = st.columns(2)
        if cy.button("✅ " + _t("ยืนยัน","Yes, Delete"), key=f"cit_del_yes{suffix}"):
            with get_sync_db() as db:
                try:
                    db.execute(text("UPDATE citizens SET is_deleted=true WHERE id=:id"),
                               {"id": sel_id})
                except Exception:
                    obj = db.get(Citizen, sel_id)
                    if obj: db.delete(obj)
            st.session_state.pop("cit_pending_del", None)
            st.success(_t("ลบสำเร็จ","Deleted.")); st.rerun()
        if cn.button("❌ " + _t("ยกเลิก","Cancel"), key=f"cit_del_no{suffix}"):
            st.session_state.pop("cit_pending_del", None); st.rerun()

    # ── Add button at BOTTOM ──────────────────────────────────────────────────
    st.divider()
    if st.button("➕ " + _t("เพิ่มประชาชนใหม่","Add New Citizen"),
                 key=f"cit_add_btn{suffix}", type="primary", use_container_width=True):
        st.session_state["cit_mode"] = "add"; st.rerun()


# ── Elderly dedicated view ────────────────────────────────────────────────────
def _render_elderly():
    """Elderly-specific search + profile view."""
    st.markdown("### 👴 " + _t("ค้นหาผู้สูงอายุ","Elderly Citizen Search"))
    st.caption(_t(
        "ค้นหาผู้สูงอายุด้วยเงื่อนไขต่างๆ รวมถึงชื่อ อายุ โรคประจำตัว สถานะ และความเปราะบาง",
        "Search elderly citizens by name, age, chronic conditions, status and vulnerability."
    ))
    _render_list(elderly_only=True)


# ── Add / Edit form ───────────────────────────────────────────────────────────
def _citizen_form(form_key: str, rec):
    actor  = get_current_user().email if get_current_user() else "system"
    _gl    = gender_labels()
    is_th  = _is_th()

    # Auto-generate citizen code for new records
    default_code = ""
    if not rec:
        comm_code = st.text_input(
            _t("รหัสชุมชน (ใช้สำหรับ running number เช่น A, B, CM)","Community Code (prefix)"),
            value="A", max_chars=5, key=form_key+"_comm"
        )
        default_code = _next_citizen_code(comm_code.strip().upper() or "A")
        st.info(_t(f"รหัสประชาชนที่จะใช้: **{default_code}**",
                   f"Citizen code will be: **{default_code}**"))

    with st.form(form_key):
        st.markdown("##### " + _t("ข้อมูลส่วนตัว","Personal Information"))
        c0,c00 = st.columns(2)
        cit_code = c0.text_input(_t("รหัสประชาชน","Citizen Code"),
                                  value=getattr(rec,"citizen_code","") or default_code if rec else default_code)
        name     = c00.text_input(_t("ชื่อ-นามสกุล *","Full Name *"),
                                   value=rec.full_name if rec else "")
        c1,c2 = st.columns(2)
        g_opts = [e.value for e in Gender]
        cur_g  = rec.gender if rec and rec.gender in g_opts else g_opts[0]
        gender = c1.selectbox(_t("เพศ","Gender"), g_opts,
                               index=g_opts.index(cur_g),
                               format_func=lambda x: _gl.get(x,x))
        phone  = c2.text_input(_t("โทรศัพท์","Phone"),
                                value=rec.phone or "" if rec else "")
        c3,c4 = st.columns(2)
        dob    = be_date_input(
            _t("วันเกิด (DD/MM/YYYY พ.ศ.)","Date of Birth (DD/MM/YYYY)"),
            value=rec.date_of_birth if rec and rec.date_of_birth else date(1970,1,1),
            key=form_key+"_dob"
        )
        occ    = c4.text_input(_t("อาชีพ","Occupation"),
                                value=rec.occupation or "" if rec else "")
        edu    = st.text_input(_t("การศึกษา","Education"),
                                value=rec.education or "" if rec and hasattr(rec,"education") else "")

        st.markdown("##### " + _t("ที่อยู่","Address"))
        a1,a2,a3 = st.columns(3)
        house    = a1.text_input(_t("บ้านเลขที่","House No."),
                                  value=getattr(rec,"house_number","") or "" if rec else "")
        village  = a2.text_input(_t("หมู่บ้าน/ชุมชน","Village"),
                                  value=getattr(rec,"village","") or "" if rec else "")
        district = a3.text_input(_t("อำเภอ","District"),
                                  value=getattr(rec,"district","") or "" if rec else "")
        address  = st.text_area(_t("ที่อยู่เต็ม","Full Address"),
                                 value=getattr(rec,"address","") or "" if rec else "")

        st.markdown("##### " + _t("กลุ่มเปราะบาง","Vulnerability Flags"))
        fc1,fc2,fc3,fc4,fc5 = st.columns(5)
        elderly   = fc1.checkbox("👴 "+_t("ผู้สูงอายุ","Elderly"),
                                  value=bool(rec.is_elderly)      if rec else False)
        disabled  = fc2.checkbox("♿ "+_t("ผู้พิการ","Disabled"),
                                  value=bool(rec.is_disabled)     if rec else False)
        bedridden = fc3.checkbox("🛏️ "+_t("ติดเตียง","Bedridden"),
                                  value=bool(rec.is_bedridden)    if rec else False)
        pregnant  = fc4.checkbox("🤰 "+_t("ตั้งครรภ์","Pregnant"),
                                  value=bool(rec.is_pregnant)     if rec else False)
        alone     = fc5.checkbox("🏠 "+_t("อยู่คนเดียว","Lives Alone"),
                                  value=bool(rec.is_living_alone) if rec else False)
        notes     = st.text_area(_t("หมายเหตุ","Notes"),
                                  value=getattr(rec,"notes","") or "" if rec else "")

        sub = st.form_submit_button(
            _t("💾 บันทึก","💾 Save"), type="primary", use_container_width=True
        )

    if sub and name:
        with get_sync_db() as db:
            if rec:
                obj = db.get(Citizen, str(rec.id))
                if obj:
                    obj.full_name=name; obj.gender=gender; obj.date_of_birth=dob
                    obj.phone=phone or None; obj.occupation=occ or None
                    obj.education=edu or None
                    obj.is_elderly=elderly; obj.is_disabled=disabled
                    obj.is_bedridden=bedridden; obj.is_pregnant=pregnant
                    obj.is_living_alone=alone; obj.updated_by=actor
                    try:
                        db.execute(text("""
                            UPDATE citizens SET
                                citizen_code=:cc, house_number=:hn, village=:vl,
                                district=:dist, address=:addr, notes=:notes,
                                national_id=:nid
                            WHERE id=:id
                        """), {"cc":cit_code or None,"hn":house or None,"vl":village or None,
                               "dist":district or None,"addr":address or None,
                               "notes":notes or None,
                               "nid":nid.replace("-","") if nid and len(nid.replace("-",""))==13 else None,
                               "id":str(rec.id)})
                    except Exception: pass
                st.success(_t("แก้ไขสำเร็จ","Updated successfully."))
            else:
                new_c = Citizen(
                    full_name=name, gender=gender, date_of_birth=dob,
                    phone=phone or None, occupation=occ or None, education=edu or None,
                    is_elderly=elderly, is_disabled=disabled, is_bedridden=bedridden,
                    is_pregnant=pregnant, is_living_alone=alone,
                    created_by=actor, updated_by=actor
                )
                db.add(new_c); db.flush()
                try:
                    db.execute(text("""
                        UPDATE citizens SET
                            citizen_code=:cc, house_number=:hn, village=:vl,
                            district=:dist, address=:addr, notes=:notes,
                            national_id=:nid
                        WHERE id=:id
                    """), {"cc":cit_code or None,"hn":house or None,"vl":village or None,
                           "dist":district or None,"addr":address or None,
                           "notes":notes or None,
                           "nid":nid.replace("-","") if nid and len(nid.replace("-",""))==13 else None,
                           "id":str(new_c.id)})
                except Exception: pass
                st.success(_t(f"เพิ่มประชาชน '{name}' สำเร็จ รหัส: {cit_code}",
                               f"Citizen '{name}' added. Code: {cit_code}"))
        set_list("cit"); st.rerun()
    elif sub:
        st.warning(_t("กรุณากรอกชื่อ-นามสกุล","Name is required."))
