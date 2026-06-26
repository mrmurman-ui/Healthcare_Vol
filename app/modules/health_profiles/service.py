"""Health Profile — with full Thai/EN language support."""
from __future__ import annotations
import uuid
import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.health_profiles.model import HealthProfile

BLOOD_TYPES = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]

# ── Bilingual label map ───────────────────────────────────────────────────────
L = {
    # Page / Search
    "title":           ("โปรไฟล์สุขภาพ",              "Health Profiles"),
    "search":          ("ค้นหาชื่อประชาชน",              "Search Citizen Name"),
    "no_citizens":     ("ไม่พบประชาชน กรุณาค้นหาด้านบน","No citizens found. Search above."),
    "select_citizen":  ("เลือกประชาชน",                  "Select Citizen"),
    "profile_for":     ("โปรไฟล์สุขภาพ",                 "Health Profile"),
    # KPIs
    "chronic_count":   ("จำนวนโรคเรื้อรัง",              "Chronic Conditions"),
    "needs_caregiver": ("ต้องการผู้ดูแล",                 "Needs Caregiver"),
    "service_needs":   ("ความต้องการบริการ",              "Service Needs"),
    "yes":             ("ใช่",                           "Yes"),
    "no":              ("ไม่ใช่",                        "No"),
    # Sections
    "basic_info":      ("ข้อมูลพื้นฐาน",                  "Basic Info"),
    "chronic":         ("โรคเรื้อรัง (รายงานตนเอง)",       "Chronic Conditions (self-reported)"),
    "functional":      ("สถานะการเคลื่อนไหว",              "Functional Status"),
    "social":          ("สุขภาพทางสังคม",                  "Social Health"),
    "home_env":        ("สภาพแวดล้อมที่บ้าน",              "Home Environment"),
    "service_needs_sec":("ความต้องการบริการ",              "Service Needs"),
    # Basic fields
    "blood_type":      ("หมู่เลือด",                      "Blood Type"),
    "caregiver":       ("ชื่อผู้ดูแลหลัก",                "Primary Caregiver"),
    "caregiver_phone": ("เบอร์โทรผู้ดูแล",                "Caregiver Phone"),
    "allergies":       ("การแพ้ยา/อาหาร",                 "Allergies"),
    "medication":      ("บันทึกยา",                       "Medication Notes"),
    # Chronic conditions
    "diabetes":        ("เบาหวาน",                       "Diabetes"),
    "hypertension":    ("ความดันโลหิตสูง",                "Hypertension"),
    "dyslipidemia":    ("ไขมันในเลือดสูง",                "Dyslipidemia"),
    "heart_disease":   ("โรคหัวใจ",                      "Heart Disease"),
    "stroke":          ("โรคหลอดเลือดสมอง",               "Stroke"),
    "cancer":          ("มะเร็ง",                         "Cancer"),
    "kidney":          ("โรคไต",                          "Kidney Disease"),
    "lung":            ("โรคปอด",                         "Lung Disease"),
    "other_cond":      ("โรคอื่นๆ",                       "Other Conditions"),
    # Functional
    "walks":           ("เดินได้ปกติ",                    "Walks Independently"),
    "cane":            ("ใช้ไม้เท้า",                     "Uses Cane"),
    "walker":          ("ใช้อุปกรณ์พยุงเดิน",             "Uses Walker"),
    "wheelchair":      ("ใช้รถเข็น",                      "Wheelchair"),
    "homebound":       ("ติดบ้าน",                        "Homebound"),
    "bedridden":       ("ติดเตียง",                       "Bedridden"),
    # Social
    "lives_alone":     ("อยู่คนเดียว",                    "Lives Alone"),
    "has_caregiver":   ("มีผู้ดูแล",                      "Has Caregiver"),
    "income":          ("ปัญหารายได้",                    "Income Problems"),
    "food":            ("ขาดแคลนอาหาร",                   "Food Insecurity"),
    "social_iso":      ("โดดเดี่ยวทางสังคม",               "Social Isolation"),
    "healthcare_acc":  ("ปัญหาการเข้าถึงบริการ",           "Healthcare Access Issues"),
    # Home environment
    "unsafe_bath":     ("ห้องน้ำไม่ปลอดภัย",               "Unsafe Bathroom"),
    "slippery":        ("พื้นลื่น",                       "Slippery Floor"),
    "poor_light":      ("แสงสว่างไม่เพียงพอ",              "Poor Lighting"),
    "unsafe_stairs":   ("บันไดไม่ปลอดภัย",                "Unsafe Stairs"),
    "electrical":      ("อันตรายไฟฟ้า",                   "Electrical Hazards"),
    "structural":      ("ความเสียหายโครงสร้าง",            "Structural Damage"),
    # Service needs
    "need_visit":      ("ต้องการเยี่ยมบ้าน",               "Home Visit"),
    "need_transport":  ("ต้องการพาหนะ",                   "Transportation"),
    "need_welfare":    ("ต้องการสวัสดิการ",                "Welfare Assistance"),
    "need_home_mod":   ("ปรับปรุงที่อยู่อาศัย",            "Home Modification"),
    "need_equip":      ("ต้องการอุปกรณ์",                  "Equipment Support"),
    "need_social":     ("ต้องการสนับสนุนทางสังคม",         "Social Support"),
    # Buttons
    "save":            ("💾 บันทึก",                      "💾 Save"),
    "saved":           ("บันทึกสำเร็จ",                   "Health profile saved."),
}


def _tc(key: str) -> str:
    """Look up from L dict — Thai or EN based on session state."""
    is_thai = st.session_state.get("lang", "TH") == "TH"
    pair = L.get(key, (key, key))
    return pair[0] if is_thai else pair[1]


def _t(th: str, en: str) -> str:
    """Return Thai or EN string directly."""
    return th if st.session_state.get("lang", "TH") == "TH" else en


def get_or_create_profile(db: Session, citizen_id: uuid.UUID) -> HealthProfile:
    profile = db.execute(
        select(HealthProfile).where(HealthProfile.citizen_id == citizen_id)
    ).scalar_one_or_none()
    if not profile:
        profile = HealthProfile(
            citizen_id=citizen_id,
            created_by="system", updated_by="system",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def chronic_condition_count(profile: HealthProfile) -> int:
    return sum(1 for c in [
        profile.has_diabetes, profile.has_hypertension, profile.has_dyslipidemia,
        profile.has_heart_disease, profile.has_stroke, profile.has_cancer,
        profile.has_kidney_disease, profile.has_lung_disease,
    ] if c)


def render_health_profiles() -> None:
    is_thai = st.session_state.get("lang", "TH") == "TH"

    search = st.text_input(_tc("search"), key="hp_search")
    with get_sync_db() as db:
        stmt = select(Citizen)
        if search:
            stmt = stmt.where(Citizen.full_name.ilike(f"%{search}%"))
        citizens = db.execute(stmt.limit(50)).scalars().all()

    if not citizens:
        st.info(_tc("no_citizens"))
        return

    options = {f"{c.full_name} (ID: {str(c.id)[:8]})": c.id for c in citizens}
    selected_label = st.selectbox(_tc("select_citizen"), list(options.keys()))
    citizen_id = options[selected_label]

    with get_sync_db() as db:
        citizen = db.get(Citizen, citizen_id)
        profile = get_or_create_profile(db, citizen_id)

        st.subheader(f"{_tc('profile_for')} — {citizen.full_name}")

        # ── Enterprise KPI cards ──────────────────────────────────────────────
        is_thai_hp = st.session_state.get("lang","TH") == "TH"
        chronic_n = chronic_condition_count(profile)
        needs_cg = not profile.has_caregiver and profile.lives_alone_profile
        service_n = sum([
            profile.needs_home_visit or False,
            profile.needs_transportation or False,
            profile.needs_welfare_assistance or False,
            profile.needs_home_modification or False,
            profile.needs_equipment_support or False,
            profile.needs_social_support or False,
        ])
        is_homebound = profile.is_homebound or profile.is_bedridden_profile
        blood_t = profile.blood_type or (_t("ไม่ระบุ","Unknown"))

        kpi_icons = {
            "chronic": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="1.8"><path d="M19 14c1.5-1 3-2.5 3-5a6 6 0 0 0-12 0c0 2.5 1.5 4 3 5"/><rect x="7" y="14" width="10" height="8" rx="2"/><line x1="12" y1="17" x2="12" y2="19"/><line x1="10" y1="18" x2="14" y2="18"/></svg>',
            "caregiver":'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="1.8"><circle cx="9" cy="7" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6"/><circle cx="17" cy="10" r="2"/><path d="M17 14v1l1 1"/><circle cx="17" cy="18" r="3"/></svg>',
            "service":  '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="1.8"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>',
            "blood":    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="1.8"><path d="M12 2L8 8H4l4 6H4l8 8 8-8h-4l4-6h-4z"/></svg>',
            "mobility": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="1.8"><circle cx="12" cy="5" r="2"/><path d="M12 7v6l4 4M12 13l-4 4"/><line x1="8" y1="21" x2="12" y2="17"/></svg>',
            "home":     '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="1.8"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9,22 9,12 15,12 15,22"/></svg>',
        }

        def _hp_card(icon_key, label, value, color, sub=""):
            bg_map = {"red":"#FEF2F2","purple":"#F5F3FF","green":"#F0FDF4",
                      "blue":"#EFF6FF","amber":"#FFFBEB","teal":"#F0FDFA"}
            border_map = {"red":"#FECACA","purple":"#DDD6FE","green":"#BBF7D0",
                          "blue":"#BFDBFE","amber":"#FDE68A","teal":"#99F6E4"}
            txt_map = {"red":"#DC2626","purple":"#7C3AED","green":"#059669",
                       "blue":"#2563EB","amber":"#D97706","teal":"#0D9488"}
            return (
                f'<div style="background:white;border-radius:16px;padding:20px 18px 16px;'
                f'box-shadow:0 2px 12px rgba(15,23,42,0.06),0 0 0 1px #F1F5F9;flex:1;min-width:0;">'
                f'<div style="width:44px;height:44px;border-radius:50%;background:{bg_map[color]};'
                f'border:1px solid {border_map[color]};display:flex;align-items:center;'
                f'justify-content:center;margin-bottom:14px;">{kpi_icons[icon_key]}</div>'
                f'<div style="font-size:13px;font-weight:500;color:#64748B;margin-bottom:6px;">{label}</div>'
                f'<div style="font-size:28px;font-weight:800;color:#0F172A;line-height:1;">{value}</div>'
                f'{"<div style=\"font-size:11px;color:#94A3B8;margin-top:6px;\">"+sub+"</div>" if sub else ""}'
                f'</div>'
            )

        is_homebound_label = _t("ติดบ้าน","Homebound") if is_homebound else _t("เคลื่อนไหวได้","Mobile")
        mobility_color = "amber" if is_homebound else "blue"

        kpi_html = (
            f'<div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;">'
            + _hp_card("chronic",  _t("โรคเรื้อรัง","Chronic Conditions"),     chronic_n,  "red",
                       _t("โรค","conditions") if chronic_n > 0 else _t("ไม่พบ","None found"))
            + _hp_card("caregiver",_t("ต้องการผู้ดูแล","Needs Caregiver"),
                       _t("ใช่","Yes") if needs_cg else _t("ไม่ใช่","No"),
                       "purple" if needs_cg else "green",
                       _t("อยู่คนเดียว ไม่มีผู้ดูแล","Lives alone, no caregiver") if needs_cg else _t("มีผู้ดูแล","Caregiver assigned"))
            + _hp_card("service",  _t("ความต้องการบริการ","Service Needs"),     service_n,  "green",
                       _t(f"{service_n} รายการ",f"{service_n} items needed") if service_n > 0 else _t("ไม่มี","None"))
            + _hp_card("blood",    _t("หมู่เลือด","Blood Type"),               blood_t,    "red",
                       _t("ข้อมูลพื้นฐาน","Basic info"))
            + _hp_card("mobility", _t("สถานะการเคลื่อนไหว","Mobility Status"), is_homebound_label, mobility_color,
                       _t("ติดบ้านหรือติดเตียง","Homebound or bedridden") if is_homebound else _t("เดินได้ปกติ","Walks independently"))
            + _hp_card("home",     _t("ความต้องการเยี่ยมบ้าน","Visit Need"),
                       _t("ต้องการ","Required") if profile.needs_home_visit else _t("ไม่ต้องการ","Not required"),
                       "amber" if profile.needs_home_visit else "teal",
                       _t("กำหนดเยี่ยมบ้านโดยเร็ว","Schedule visit soon") if profile.needs_home_visit else "")
            + f'</div>'
        )
        st.markdown(kpi_html, unsafe_allow_html=True)

        st.divider()

        with st.form("edit_profile"):

            # ── Basic Info ────────────────────────────────────────────────────
            st.subheader(_tc("basic_info"))
            col1, col2 = st.columns(2)
            blood_type = col1.selectbox(
                _tc("blood_type"), BLOOD_TYPES,
                index=BLOOD_TYPES.index(profile.blood_type or ""),
            )
            primary_caregiver = col2.text_input(
                _tc("caregiver"), value=profile.primary_caregiver or ""
            )
            caregiver_phone = col1.text_input(
                _tc("caregiver_phone"), value=profile.caregiver_phone or ""
            )
            allergies = st.text_area(_tc("allergies"), value=profile.allergies or "")
            medication_notes = st.text_area(_tc("medication"), value=profile.medication_notes or "")

            # ── Chronic Conditions ────────────────────────────────────────────
            st.subheader(_tc("chronic"))
            cc1, cc2, cc3, cc4 = st.columns(4)
            has_diabetes     = cc1.checkbox(_tc("diabetes"),     value=profile.has_diabetes or False)
            has_hypertension = cc2.checkbox(_tc("hypertension"), value=profile.has_hypertension or False)
            has_dyslipidemia = cc3.checkbox(_tc("dyslipidemia"), value=profile.has_dyslipidemia or False)
            has_heart        = cc4.checkbox(_tc("heart_disease"),value=profile.has_heart_disease or False)
            cc5, cc6, cc7, cc8 = st.columns(4)
            has_stroke  = cc5.checkbox(_tc("stroke"),  value=profile.has_stroke or False)
            has_cancer  = cc6.checkbox(_tc("cancer"),  value=profile.has_cancer or False)
            has_kidney  = cc7.checkbox(_tc("kidney"),  value=profile.has_kidney_disease or False)
            has_lung    = cc8.checkbox(_tc("lung"),    value=profile.has_lung_disease or False)
            other_conditions = st.text_input(_tc("other_cond"), value=profile.other_conditions or "")

            # ── Functional Status ─────────────────────────────────────────────
            st.subheader(_tc("functional"))
            fs1, fs2, fs3 = st.columns(3)
            walks           = fs1.checkbox(_tc("walks"),      value=profile.walks_independently or False)
            uses_cane       = fs2.checkbox(_tc("cane"),       value=profile.uses_cane or False)
            uses_walker     = fs3.checkbox(_tc("walker"),     value=profile.uses_walker or False)
            fs4, fs5, fs6 = st.columns(3)
            uses_wheelchair = fs4.checkbox(_tc("wheelchair"), value=profile.uses_wheelchair or False)
            is_homebound    = fs5.checkbox(_tc("homebound"),  value=profile.is_homebound or False)
            is_bedridden    = fs6.checkbox(_tc("bedridden"),  value=profile.is_bedridden_profile or False)

            # ── Social Health ─────────────────────────────────────────────────
            st.subheader(_tc("social"))
            sh1, sh2, sh3 = st.columns(3)
            lives_alone      = sh1.checkbox(_tc("lives_alone"),    value=profile.lives_alone_profile or False)
            has_caregiver    = sh2.checkbox(_tc("has_caregiver"),  value=profile.has_caregiver or False)
            income_problems  = sh3.checkbox(_tc("income"),         value=profile.has_income_problems or False)
            sh4, sh5, sh6 = st.columns(3)
            food_insecurity  = sh4.checkbox(_tc("food"),           value=profile.has_food_insecurity or False)
            social_isolation = sh5.checkbox(_tc("social_iso"),     value=profile.has_social_isolation or False)
            healthcare_acc   = sh6.checkbox(_tc("healthcare_acc"), value=profile.has_healthcare_access_issues or False)

            # ── Home Environment ──────────────────────────────────────────────
            st.subheader(_tc("home_env"))
            he1, he2, he3 = st.columns(3)
            unsafe_bath    = he1.checkbox(_tc("unsafe_bath"),  value=profile.unsafe_bathroom or False)
            slippery       = he2.checkbox(_tc("slippery"),     value=profile.slippery_floor or False)
            poor_light     = he3.checkbox(_tc("poor_light"),   value=profile.poor_lighting or False)
            he4, he5, he6 = st.columns(3)
            unsafe_stairs  = he4.checkbox(_tc("unsafe_stairs"),value=profile.unsafe_stairs or False)
            electrical     = he5.checkbox(_tc("electrical"),   value=profile.electrical_hazards or False)
            structural     = he6.checkbox(_tc("structural"),   value=profile.structural_damage or False)

            # ── Service Needs ─────────────────────────────────────────────────
            st.subheader(_tc("service_needs_sec"))
            sn1, sn2, sn3 = st.columns(3)
            needs_visit     = sn1.checkbox(_tc("need_visit"),    value=profile.needs_home_visit or False)
            needs_transport = sn2.checkbox(_tc("need_transport"),value=profile.needs_transportation or False)
            needs_welfare   = sn3.checkbox(_tc("need_welfare"),  value=profile.needs_welfare_assistance or False)
            sn4, sn5, sn6 = st.columns(3)
            needs_home_mod  = sn4.checkbox(_tc("need_home_mod"), value=profile.needs_home_modification or False)
            needs_equipment = sn5.checkbox(_tc("need_equip"),    value=profile.needs_equipment_support or False)
            needs_social    = sn6.checkbox(_tc("need_social"),   value=profile.needs_social_support or False)

            submitted = st.form_submit_button(_tc("save"), type="primary",
                                               use_container_width=True)

        if submitted:
            user = get_current_user()
            actor = user.email if user else "system"
            with get_sync_db() as db2:
                p = db2.get(HealthProfile, profile.id)
                p.blood_type               = blood_type or None
                p.primary_caregiver        = primary_caregiver or None
                p.caregiver_phone          = caregiver_phone or None
                p.allergies                = allergies or None
                p.medication_notes         = medication_notes or None
                p.has_diabetes             = has_diabetes
                p.has_hypertension         = has_hypertension
                p.has_dyslipidemia         = has_dyslipidemia
                p.has_heart_disease        = has_heart
                p.has_stroke               = has_stroke
                p.has_cancer               = has_cancer
                p.has_kidney_disease       = has_kidney
                p.has_lung_disease         = has_lung
                p.other_conditions         = other_conditions or None
                p.walks_independently      = walks
                p.uses_cane                = uses_cane
                p.uses_walker              = uses_walker
                p.uses_wheelchair          = uses_wheelchair
                p.is_homebound             = is_homebound
                p.is_bedridden_profile     = is_bedridden
                p.lives_alone_profile      = lives_alone
                p.has_caregiver            = has_caregiver
                p.has_income_problems      = income_problems
                p.has_food_insecurity      = food_insecurity
                p.has_social_isolation     = social_isolation
                p.has_healthcare_access_issues = healthcare_acc
                p.unsafe_bathroom          = unsafe_bath
                p.slippery_floor           = slippery
                p.poor_lighting            = poor_light
                p.unsafe_stairs            = unsafe_stairs
                p.electrical_hazards       = electrical
                p.structural_damage        = structural
                p.needs_home_visit         = needs_visit
                p.needs_transportation     = needs_transport
                p.needs_welfare_assistance = needs_welfare
                p.needs_home_modification  = needs_home_mod
                p.needs_equipment_support  = needs_equipment
                p.needs_social_support     = needs_social
                p.updated_by               = actor
                db2.commit()
            st.success("✅ " + _tc("saved"))
            st.rerun()
