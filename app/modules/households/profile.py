"""Household Profile — full view with family members linked to citizen records."""
from __future__ import annotations
from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import select, text

from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.households.model import Household
from app.shared.date_utils import fmt_date, be_date_input, ad_to_be_year

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en


def _calc_age(dob) -> int | None:
    if dob is None: return None
    try:
        from datetime import datetime
        born = dob if hasattr(dob,"year") else datetime.strptime(str(dob)[:10],"%Y-%m-%d").date()
        t = date.today()
        return t.year - born.year - ((t.month,t.day)<(born.month,born.day))
    except: return None


def _ensure_members_table():
    """Create household_members table for extra members not yet in citizens."""
    with get_sync_db() as db:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS household_members (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                citizen_id UUID REFERENCES citizens(id) ON DELETE SET NULL,
                full_name VARCHAR(200) NOT NULL,
                relation VARCHAR(50),
                date_of_birth VARCHAR(20),
                gender VARCHAR(10),
                occupation VARCHAR(100),
                education VARCHAR(100),
                phone VARCHAR(20),
                notes TEXT,
                is_deleted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                created_by VARCHAR(100),
                updated_by VARCHAR(100)
            )
        """))


RELATIONS_TH = {
    "head":"หัวหน้าครัวเรือน","spouse":"คู่สมรส","child":"บุตร/บุตรี",
    "parent":"บิดา/มารดา","sibling":"พี่น้อง","grandparent":"ปู่/ย่า/ตา/ยาย",
    "grandchild":"หลาน","other":"อื่นๆ",
}
RELATIONS_EN = {k: v for k,v in {
    "head":"Head","spouse":"Spouse","child":"Child","parent":"Parent",
    "sibling":"Sibling","grandparent":"Grandparent","grandchild":"Grandchild","other":"Other"
}.items()}
GENDER_TH = {"male":"ชาย","female":"หญิง","other":"อื่นๆ"}


def render_household_profile(household_id: str) -> None:
    _ensure_members_table()
    is_th = _t("th","en") == "th"

    with get_sync_db() as db:
        hh = db.get(Household, household_id)
        if not hh:
            st.error(_t("ไม่พบข้อมูลครัวเรือน","Household not found."))
            return

        # Linked citizens (via household_id FK)
        linked_cits = db.execute(
            select(Citizen).where(Citizen.household_id == hh.id)
        ).scalars().all()

        # Extra household members
        members = db.execute(text("""
            SELECT id, full_name, relation, date_of_birth, gender,
                   occupation, education, phone, citizen_id, notes
            FROM household_members
            WHERE household_id=:hid AND (is_deleted IS NULL OR is_deleted=false)
            ORDER BY created_at
        """), {"hid": str(household_id)}).fetchall()

        # Visit history for this household
        visits = db.execute(text("""
            SELECT hv.visit_date, hv.visit_type, c.full_name, hv.observation
            FROM home_visits hv
            LEFT JOIN citizens c ON c.id = hv.citizen_id
            WHERE c.household_id = :hid
            ORDER BY hv.visit_date DESC LIMIT 10
        """), {"hid": str(household_id)}).fetchall()

    # ── Back ──────────────────────────────────────────────────────────────────
    if st.button("← " + _t("ย้อนกลับ","Back"), key="hh_prof_back"):
        st.session_state.pop("hh_profile_id", None)
        st.rerun()

    st.divider()

    # ── Hero card ─────────────────────────────────────────────────────────────
    INCOME_TH = {"very_low":"รายได้น้อยมาก","low":"รายได้น้อย","medium":"รายได้ปานกลาง","high":"รายได้สูง"}
    HOUSING_TH = {"own":"บ้านตัวเอง","rent":"เช่า","free":"อาศัยฟรี","other":"อื่นๆ"}
    inc  = INCOME_TH.get(hh.income_group or "","—") if is_th else (hh.income_group or "—")
    hou  = HOUSING_TH.get(hh.housing_type or "","—") if is_th else (hh.housing_type or "—")

    st.markdown(f"""
<div style="background:linear-gradient(135deg,#065F46,#059669);
  border-radius:16px;padding:28px 32px;color:white;margin-bottom:16px">
  <div style="font-size:28px;font-weight:800">{hh.household_code}</div>
  <div style="font-size:18px;margin:6px 0">🏠 {hh.head_of_household or '—'}</div>
  <div style="font-size:14px;opacity:0.85">
    📍 {hh.address or ''} {hh.village or ''} {hh.district or ''} {hh.province or ''}<br>
    📞 {hh.phone or '—'} &nbsp;·&nbsp; 💰 {inc} &nbsp;·&nbsp; 🏡 {hou}
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Quick stats ────────────────────────────────────────────────────────────
    total_members = len(linked_cits) + len(members)
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric(_t("สมาชิกทั้งหมด","Total Members"), total_members)
    sc2.metric(_t("ในระบบ","In System"),             len(linked_cits))
    sc3.metric(_t("เพิ่มเติม","Additional"),          len(members))
    sc4.metric(_t("การเยี่ยมบ้าน","Visits"),          len(visits))

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_mem, tab_add, tab_visits = st.tabs([
        "👨‍👩‍👧‍👦 " + _t("สมาชิกครอบครัว","Family Members"),
        "➕ " + _t("เพิ่มสมาชิก","Add Member"),
        "🏠 " + _t("ประวัติการเยี่ยม","Visit History"),
    ])

    # ── Tab 1: Members ────────────────────────────────────────────────────────
    with tab_mem:
        # Citizens linked via household_id
        if linked_cits:
            st.markdown("**👤 " + _t("ประชาชนที่ลงทะเบียนในระบบ","Registered Citizens") + "**")
            rows = []
            for c in linked_cits:
                age = _calc_age(c.date_of_birth)
                flags = ""
                if c.is_elderly:   flags += "👴"
                if c.is_disabled:  flags += "♿"
                if c.is_bedridden: flags += "🛏️"
                rows.append({
                    _t("ชื่อ","Name"):          c.full_name,
                    _t("เพศ","Gender"):         GENDER_TH.get(c.gender or "","") if is_th else (c.gender or ""),
                    _t("อายุ","Age"):            f"{age} {_t('ปี','y')}" if age else "—",
                    _t("วันเกิด","DOB"):        fmt_date(c.date_of_birth),
                    _t("อาชีพ","Occupation"):   c.occupation or "—",
                    _t("กลุ่ม","Flags"):        flags if flags else "—",
                    _t("โทร","Phone"):           c.phone or "—",
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Clickable to view profile
            sel_name_opts = {f"{c.full_name}": str(c.id) for c in linked_cits}
            sel_n = st.selectbox(_t("ดูโปรไฟล์ประชาชน","View Citizen Profile"),
                                  list(sel_name_opts.keys()), key="hh_cit_sel")
            if st.button("👤 " + _t("เปิดโปรไฟล์","Open Profile"), key="hh_open_prof"):
                st.session_state["cit_profile_id"] = sel_name_opts[sel_n]
                st.session_state["nav_from_hh"]    = str(household_id)
                st.rerun()

        # Extra members
        if members:
            st.divider()
            st.markdown("**📝 " + _t("สมาชิกที่เพิ่มเติม","Additional Members") + "**")
            mrows = []
            for m in members:
                age = _calc_age(m[3])
                rel = RELATIONS_TH.get(m[2] or "","") if is_th else (RELATIONS_EN.get(m[2] or "","") or m[2] or "")
                mrows.append({
                    _t("ชื่อ","Name"):          m[1],
                    _t("ความสัมพันธ์","Relation"): rel,
                    _t("เพศ","Gender"):         GENDER_TH.get(m[4] or "","") if is_th else (m[4] or ""),
                    _t("อายุ","Age"):            f"{age} {_t('ปี','y')}" if age else "—",
                    _t("อาชีพ","Occupation"):   m[5] or "—",
                    _t("การศึกษา","Education"): m[6] or "—",
                    _t("โทร","Phone"):           m[7] or "—",
                })
            st.dataframe(pd.DataFrame(mrows), use_container_width=True, hide_index=True)

            # Delete member
            del_opts = {m[1]: str(m[0]) for m in members}
            del_sel  = st.selectbox(_t("เลือกสมาชิกเพื่อลบ","Select to Delete"),
                                     list(del_opts.keys()), key="hh_del_mem")
            if st.button("🗑️ " + _t("ลบสมาชิก","Delete Member"), key="hh_do_del_mem"):
                with get_sync_db() as db:
                    db.execute(text(
                        "UPDATE household_members SET is_deleted=true WHERE id=:id"
                    ), {"id": del_opts[del_sel]})
                st.success(_t("ลบสำเร็จ","Deleted.")); st.rerun()

        if not linked_cits and not members:
            st.info(_t("ยังไม่มีสมาชิกในครัวเรือนนี้","No members yet."))

    # ── Tab 2: Add Member ─────────────────────────────────────────────────────
    with tab_add:
        st.markdown(_t(
            "เพิ่มสมาชิกครัวเรือนที่ยังไม่ได้ลงทะเบียนเป็นประชาชนในระบบ หรือเชื่อมโยงกับประชาชนที่มีอยู่แล้ว",
            "Add a household member who is not yet a registered citizen, or link to an existing one."
        ))

        # Option to link existing citizen
        with get_sync_db() as db:
            all_cits = db.execute(
                select(Citizen).order_by(Citizen.full_name).limit(500)
            ).scalars().all()

        cit_link_opts = {_t("— ไม่เชื่อมโยง —","— None —"): None}
        cit_link_opts.update({f"{c.full_name} ({fmt_date(c.date_of_birth)})": str(c.id)
                               for c in all_cits})

        with st.form("hh_add_member"):
            st.markdown("**" + _t("เชื่อมโยงกับประชาชนที่มีอยู่ (ไม่บังคับ)","Link to existing citizen (optional)") + "**")
            link_sel  = st.selectbox(_t("เลือกประชาชน","Select Citizen"),
                                      list(cit_link_opts.keys()), key="hh_link_cit")

            st.markdown("**" + _t("หรือกรอกข้อมูลสมาชิกใหม่","Or enter new member details") + "**")
            mc1, mc2 = st.columns(2)
            m_name  = mc1.text_input(_t("ชื่อ-นามสกุล *","Full Name *"))
            rels    = list(RELATIONS_TH.keys())
            rel_disp= [RELATIONS_TH.get(r,r) for r in rels] if is_th else [RELATIONS_EN.get(r,r) for r in rels]
            rel_sel = mc2.selectbox(_t("ความสัมพันธ์","Relation"), rel_disp)
            rel_val = rels[rel_disp.index(rel_sel)]

            mc3, mc4 = st.columns(2)
            genders   = ["male","female","other"]
            g_disp    = [GENDER_TH.get(g,g) for g in genders] if is_th else genders
            m_gender  = genders[mc3.selectbox(_t("เพศ","Gender"), range(len(g_disp)),
                                               format_func=lambda i: g_disp[i], key="hh_m_g")]
            m_dob     = be_date_input(
                _t("วันเกิด (DD/MM/YYYY พ.ศ.)","Date of Birth"),
                value=date(1980,1,1), key="hh_m_dob"
            )
            mc5, mc6 = st.columns(2)
            m_occ    = mc5.text_input(_t("อาชีพ","Occupation"))
            m_edu    = mc6.text_input(_t("การศึกษา","Education"))
            m_phone  = st.text_input(_t("โทรศัพท์","Phone"))
            m_notes  = st.text_area(_t("หมายเหตุ","Notes"))
            sub = st.form_submit_button(_t("💾 เพิ่มสมาชิก","💾 Add Member"),
                                         type="primary", use_container_width=True)

        if sub:
            actor = get_current_user().email if get_current_user() else "system"
            linked_id = cit_link_opts.get(link_sel)
            # Auto-fill name from linked citizen
            display_name = m_name
            if linked_id and not m_name:
                matched = next((c.full_name for c in all_cits if str(c.id)==linked_id), "")
                display_name = matched
            if not display_name:
                st.warning(_t("กรุณากรอกชื่อสมาชิก","Member name is required."))
            else:
                with get_sync_db() as db:
                    db.execute(text("""
                        INSERT INTO household_members
                            (id,household_id,citizen_id,full_name,relation,
                             date_of_birth,gender,occupation,education,phone,notes,
                             created_by,updated_by)
                        VALUES
                            (gen_random_uuid(),:hid,:cid,:name,:rel,
                             :dob,:gender,:occ,:edu,:phone,:notes,:actor,:actor)
                    """), {
                        "hid": str(household_id),
                        "cid": linked_id,
                        "name": display_name,
                        "rel": rel_val,
                        "dob": str(m_dob),
                        "gender": m_gender,
                        "occ": m_occ or None,
                        "edu": m_edu or None,
                        "phone": m_phone or None,
                        "notes": m_notes or None,
                        "actor": actor,
                    })
                st.success(_t(f"เพิ่มสมาชิก '{display_name}' สำเร็จ",
                               f"Member '{display_name}' added.")); st.rerun()

    # ── Tab 3: Visits ─────────────────────────────────────────────────────────
    with tab_visits:
        if visits:
            VTYPE_TH = {"routine":"ตามแผน","follow_up":"ติดตาม","emergency":"ฉุกเฉิน"}
            vrows = [{
                _t("วันที่","Date"):       fmt_date(v[0]),
                _t("ผู้รับบริการ","Citizen"): v[2] or "—",
                _t("ประเภท","Type"):       VTYPE_TH.get(v[1],v[1]) if is_th else v[1],
                _t("บันทึก","Note"):       (v[3] or "")[:60],
            } for v in visits]
            st.dataframe(pd.DataFrame(vrows), use_container_width=True, hide_index=True)
        else:
            st.info(_t("ยังไม่มีการเยี่ยมบ้านในครัวเรือนนี้","No visits for this household."))
