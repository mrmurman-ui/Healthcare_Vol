# -*- coding: utf-8 -*-
"""Health Assessments — full Thai/EN bilingual."""
from __future__ import annotations
import streamlit as st
from sqlalchemy import select
from app.core.db_sync import get_sync_db
from app.modules.auth.session import get_current_user
from app.modules.citizens.model import Citizen
from app.modules.health_assessments.model import HealthAssessment
from app.modules.volunteers.model import Volunteer
from app.shared.date_utils import be_date_input_col, fmt_date


def _t(th: str, en: str) -> str:
    return th if st.session_state.get("lang","TH") == "TH" else en


def calculate_bmi(weight: float, height: float) -> float | None:
    if weight and height and height > 0:
        return round(weight / ((height / 100) ** 2), 1)
    return None


def render_health_assessments() -> None:
    is_thai = st.session_state.get("lang","TH") == "TH"

    # ── Search citizen ────────────────────────────────────────────────────────
    search = st.text_input(_t("🔍 ค้นหาชื่อประชาชน","🔍 Search Citizen Name"), key="ha_search")
    with get_sync_db() as db:
        stmt = select(Citizen)
        if search:
            stmt = stmt.where(Citizen.full_name.ilike(f"%{search}%"))
        citizens = db.execute(stmt.limit(50)).scalars().all()

    if not citizens:
        st.info(_t("ไม่พบประชาชน กรุณาค้นหาด้านบน","No citizens found. Search above."))
        return

    opts = {f"{c.full_name} (ID: {str(c.id)[:8]})": c.id for c in citizens}
    sel  = st.selectbox(_t("เลือกประชาชน","Select Citizen"), list(opts.keys()))
    cit_id = opts[sel]

    with get_sync_db() as db:
        # Load existing assessments
        assessments = db.execute(
            select(HealthAssessment)
            .where(HealthAssessment.citizen_id == cit_id,
                   HealthAssessment.is_deleted == False)
            .order_by(HealthAssessment.assessment_date.desc())
            .limit(20)
        ).scalars().all()

        vols = db.execute(select(Volunteer).limit(100)).scalars().all()
        vol_opts = {_t("ไม่ระบุ","None"): None}
        vol_opts.update({v.full_name: v.id for v in vols})

    # ── History ───────────────────────────────────────────────────────────────
    n = len(assessments)
    hist_label = _t(f"ประวัติการประเมิน ({n} รายการ)",
                    f"Assessment History ({n} records)")
    st.subheader(hist_label)

    if assessments:
        import pandas as pd
        df = pd.DataFrame([{
            _t("วันที่","Date"): str(a.assessment_date or "")[:10],
            _t("ประเภท","Type"): _t(
                {"routine":"ปกติ","follow_up":"ติดตาม","annual":"ประจำปี"}.get(a.assessment_type or "","ปกติ"),
                a.assessment_type or "routine"
            ),
            "BMI": a.bmi,
            _t("ความดัน","BP"): f"{int(a.bp_systolic or 0)}/{int(a.bp_diastolic or 0)}",
            _t("น้ำหนัก(กก.)","Weight(kg)"): a.weight_kg,
            _t("ส่วนสูง(ซม.)","Height(cm)"): a.height_cm,
            _t("ชีพจร","Pulse"): a.pulse_rate,
            _t("อุณหภูมิ","Temp°C"): a.temperature_c,
        } for a in assessments])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(_t("ยังไม่มีประวัติการประเมิน","No assessment history yet."))

    st.divider()

    # ── New Assessment Form ───────────────────────────────────────────────────
    st.subheader(_t("➕ บันทึกการประเมินใหม่","➕ New Assessment"))

    with st.form("new_assessment_form"):
        c1, c2 = st.columns(2)
        assess_date = be_date_input_col(c1, _t("วันที่ประเมิน","Assessment Date"))
        assess_type = c2.selectbox(
            _t("ประเภทการประเมิน","Type"),
            options=["routine","follow_up","annual"],
            format_func=lambda x: {
                "routine": _t("ปกติ","Routine"),
                "follow_up": _t("ติดตาม","Follow Up"),
                "annual": _t("ประจำปี","Annual"),
            }[x]
        )
        vol_sel = c1.selectbox(_t("อาสาสมัครที่ประเมิน","Assessed By"), list(vol_opts.keys()))

        st.subheader(_t("📏 การวัด","📏 Measurements"))
        m1, m2, m3, m4 = st.columns(4)
        height   = m1.number_input(_t("ส่วนสูง (ซม.)","Height (cm)"),       0.0,250.0,0.0,0.5)
        weight   = m2.number_input(_t("น้ำหนัก (กก.)","Weight (kg)"),        0.0,200.0,0.0,0.5)
        waist    = m3.number_input(_t("รอบเอว (ซม.)","Waist (cm)"),           0.0,200.0,0.0,0.5)
        temp     = m4.number_input(_t("อุณหภูมิ (°C)","Temperature (°C)"),   35.0,42.0,36.5,0.1)

        m5, m6, m7, m8 = st.columns(4)
        bp_sys   = m5.number_input(_t("ความดัน (ตัวบน)","BP Systolic"),      0.0,300.0,120.0,1.0)
        bp_dia   = m6.number_input(_t("ความดัน (ตัวล่าง)","BP Diastolic"),   0.0,200.0,80.0, 1.0)
        pulse    = m7.number_input(_t("ชีพจร (ครั้ง/นาที)","Pulse Rate"),    0.0,250.0,72.0, 1.0)
        b_sugar  = m8.number_input(_t("น้ำตาลในเลือด (ไม่บังคับ)","Blood Sugar (optional)"), 0.0,600.0,0.0,1.0)

        bmi_val = calculate_bmi(weight, height)
        if bmi_val:
            bmi_label = _t(
                f"BMI: {bmi_val} — " + ("ผอม" if bmi_val<18.5 else "ปกติ" if bmi_val<25 else "น้ำหนักเกิน" if bmi_val<30 else "อ้วน"),
                f"BMI: {bmi_val} — " + ("Underweight" if bmi_val<18.5 else "Normal" if bmi_val<25 else "Overweight" if bmi_val<30 else "Obese")
            )
            st.info(f"🔢 {bmi_label}")

        notes = st.text_area(_t("หมายเหตุ","Notes"), height=80)
        submit = st.form_submit_button(
            _t("💾 บันทึกการประเมิน","💾 Save Assessment"),
            type="primary", use_container_width=True
        )

    if submit:
        if height == 0 or weight == 0:
            st.error(_t("กรุณากรอกส่วนสูงและน้ำหนัก","Please enter height and weight."))
            return
        actor = get_current_user().email if get_current_user() else "system"
        try:
            with get_sync_db() as db:
                db.add(HealthAssessment(
                    citizen_id=cit_id,
                    volunteer_id=vol_opts.get(vol_sel),
                    assessment_date=str(assess_date),
                    assessment_type=assess_type,
                    height_cm=height, weight_kg=weight,
                    bmi=bmi_val, waist_cm=waist or None,
                    bp_systolic=bp_sys or None, bp_diastolic=bp_dia or None,
                    pulse_rate=pulse or None, temperature_c=temp or None,
                    blood_sugar=b_sugar or None,
                    notes=notes or None,
                    created_by=actor, updated_by=actor,
                ))
            st.success("✅ " + _t("บันทึกสำเร็จ","Assessment saved."))
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
