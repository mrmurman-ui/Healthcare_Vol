"""Citizen Profile — full individual view with health history, visits, referrals."""
from __future__ import annotations
from datetime import date

import streamlit as st
from sqlalchemy import select, text

from app.core.db_sync import get_sync_db
from app.modules.citizens.model import Citizen
from app.shared.date_utils import fmt_date, ad_to_be_year

THAI_MONTHS = ["","ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.",
               "ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."]

def _be_month_label(ym_str: str) -> str:
    """Convert YYYY-MM to Thai พ.ศ. label e.g. 'ม.ค. 2569'."""
    try:
        y, m = int(ym_str[:4]), int(ym_str[5:7])
        return f"{THAI_MONTHS[m]} {ad_to_be_year(y)}"
    except Exception:
        return ym_str

def _t(th, en): return th if st.session_state.get("lang","TH")=="TH" else en


def _calc_age(dob) -> int | None:
    if dob is None: return None
    try:
        from datetime import datetime
        born = dob if hasattr(dob,"year") else datetime.strptime(str(dob)[:10],"%Y-%m-%d").date()
        t = date.today()
        return t.year - born.year - ((t.month,t.day)<(born.month,born.day))
    except: return None


def render_citizen_profile(citizen_id: str) -> None:
    """Render full profile for one citizen."""
    with get_sync_db() as db:
        cit = db.get(Citizen, citizen_id)
        if not cit:
            st.error(_t("ไม่พบข้อมูลประชาชน","Citizen not found."))
            return

        # Related data
        visits = db.execute(text("""
            SELECT visit_date, visit_type, observation, recommendation
            FROM home_visits WHERE citizen_id=:id
            ORDER BY visit_date DESC LIMIT 10
        """), {"id": citizen_id}).fetchall()

        refs = db.execute(text("""
            SELECT referral_date, target, target_name, status, reason, outcome
            FROM referrals WHERE citizen_id=:id
            ORDER BY referral_date DESC LIMIT 10
        """), {"id": citizen_id}).fetchall()

        assessments = db.execute(text("""
            SELECT assessment_date, height_cm, weight_kg, bmi,
                   bp_systolic, bp_diastolic, pulse_rate
            FROM health_assessments WHERE citizen_id=:id
              AND (is_deleted IS NULL OR is_deleted=false)
            ORDER BY assessment_date DESC LIMIT 5
        """), {"id": citizen_id}).fetchall()

        alerts = db.execute(text("""
            SELECT title, severity, status, created_at
            FROM early_warnings WHERE citizen_id=:id
              AND (is_deleted IS NULL OR is_deleted=false)
            ORDER BY created_at DESC LIMIT 5
        """), {"id": citizen_id}).fetchall()

        outcomes = db.execute(text("""
            SELECT outcome_type, evaluation_date, baseline_value,
                   current_value, outcome_status
            FROM case_outcomes WHERE citizen_id=:id
              AND (is_deleted IS NULL OR is_deleted=false)
            ORDER BY evaluation_date DESC LIMIT 5
        """), {"id": citizen_id}).fetchall()

    # ── Back button ───────────────────────────────────────────────────────────
    if st.button("← " + _t("ย้อนกลับ","Back"), key="prof_back"):
        st.session_state.pop("cit_profile_id", None)
        st.rerun()

    st.divider()

    # ── Hero card ─────────────────────────────────────────────────────────────
    age = _calc_age(cit.date_of_birth)
    age_disp = f"{age} {_t('ปี','yrs')}" if age is not None else "—"

    GENDER_TH = {"male":"ชาย","female":"หญิง","other":"อื่นๆ"}
    gender_disp = GENDER_TH.get(cit.gender or "","") if _t("th","en")=="th" else (cit.gender or "")

    flags = []
    if cit.is_elderly:      flags.append("👴 " + _t("ผู้สูงอายุ","Elderly"))
    if cit.is_disabled:     flags.append("♿ " + _t("ผู้พิการ","Disabled"))
    if cit.is_bedridden:    flags.append("🛏️ " + _t("ติดเตียง","Bedridden"))
    if cit.is_pregnant:     flags.append("🤰 " + _t("ตั้งครรภ์","Pregnant"))
    if cit.is_living_alone: flags.append("🏠 " + _t("อยู่คนเดียว","Lives Alone"))

    with st.container():
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#1B3A6B,#2563EB);
  border-radius:16px;padding:28px 32px;color:white;margin-bottom:16px">
  <div style="font-size:32px;font-weight:800;margin-bottom:6px">{cit.full_name}</div>
  <div style="font-size:16px;opacity:0.85">
    {gender_disp} &nbsp;·&nbsp; {age_disp} &nbsp;·&nbsp;
    {_t('วันเกิด','DOB')}: {fmt_date(cit.date_of_birth)}
  </div>
  <div style="margin-top:10px;font-size:14px;opacity:0.75">
    📞 {cit.phone or '—'} &nbsp;&nbsp;
    💼 {cit.occupation or '—'}
  </div>
  <div style="margin-top:10px">
    {'&nbsp;&nbsp;'.join(f'<span style="background:rgba(255,255,255,0.2);border-radius:20px;padding:4px 14px;font-size:13px">{f}</span>' for f in flags) if flags else ''}
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Info grid ─────────────────────────────────────────────────────────────
    # ── National ID — role-gated ─────────────────────────────────────────────
    from app.modules.auth.session import get_current_user as _gcu_p
    _cur_p = _gcu_p()
    _can_see_nid = _cur_p and _cur_p.role in (
        "super_admin","province_admin","district_admin",
        "subdistrict_admin","volunteer"
    )

    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        st.markdown("**📋 " + _t("ข้อมูลทั่วไป","General") + "**")
        st.markdown(f"{_t('อาชีพ','Occupation')}: **{cit.occupation or '—'}**")
        st.markdown(f"{_t('การศึกษา','Education')}: **{getattr(cit,'education',None) or '—'}**")
        # National ID display
        raw_nid = getattr(cit, "national_id", None)
        if not raw_nid:
            # Try fetching from DB (may be in extra column)
            from app.core.db_sync import get_sync_db as _gsd
            from sqlalchemy import text as _txt
            try:
                with _gsd() as _db2:
                    _row = _db2.execute(_txt(
                        "SELECT national_id FROM citizens WHERE id=:id"
                    ), {"id": str(citizen_id)}).fetchone()
                    raw_nid = _row[0] if _row else None
            except Exception:
                raw_nid = None
        if raw_nid:
            if _can_see_nid:
                # Format as x-xxxx-xxxxx-xx-x
                n = raw_nid.replace("-","")
                if len(n) == 13:
                    formatted = f"{n[0]}-{n[1:5]}-{n[5:10]}-{n[10:12]}-{n[12]}"
                else:
                    formatted = raw_nid
                st.markdown(f"**🪪 {_t('เลขบัตรประชาชน','National ID')}:** `{formatted}`")
            else:
                # Mask for viewer role
                st.markdown(f"**🪪 {_t('เลขบัตรประชาชน','National ID')}:** `x-xxxx-xxxxx-xx-x` ⛔")
    with ic2:
        st.markdown("**🏠 " + _t("ที่อยู่","Address") + "**")
        house   = getattr(cit,"house_number",None) or ""
        village = getattr(cit,"village",None) or ""
        district= getattr(cit,"district",None) or ""
        addr    = getattr(cit,"address",None) or ""
        st.markdown(f"{_t('บ้านเลขที่','House No.')}: **{house or '—'}**")
        st.markdown(f"{_t('หมู่บ้าน','Village')}: **{village or '—'}**")
        st.markdown(f"{_t('อำเภอ','District')}: **{district or '—'}**")
    with ic3:
        st.markdown("**📊 " + _t("สถิติ","Statistics") + "**")
        st.metric(_t("การเยี่ยมบ้าน","Home Visits"),  len(visits))
        st.metric(_t("การส่งต่อ","Referrals"),         len(refs))
        st.metric(_t("การประเมิน","Assessments"),       len(assessments))

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_visits, tab_refs, tab_assess, tab_alerts, tab_outcomes = st.tabs([
        "🏠 " + _t("การเยี่ยมบ้าน","Home Visits"),
        "📤 " + _t("การส่งต่อ","Referrals"),
        "🩺 " + _t("การประเมินสุขภาพ","Assessments"),
        "⚠️ " + _t("การแจ้งเตือน","Alerts"),
        "📊 " + _t("ผลลัพธ์","Outcomes"),
    ])

    with tab_visits:
        if visits:
            VTYPE_TH = {"routine":"ตามแผน","follow_up":"ติดตาม","emergency":"ฉุกเฉิน","post_referral":"หลังส่งต่อ"}
            for v in visits:
                with st.expander(f"🏠 {fmt_date(v[0])} — {VTYPE_TH.get(v[1],v[1]) if _t('th','en')=='th' else v[1]}"):
                    if v[2]: st.markdown(f"**{_t('การสังเกต','Observation')}:** {v[2]}")
                    if v[3]: st.markdown(f"**{_t('คำแนะนำ','Recommendation')}:** {v[3]}")
        else:
            st.info(_t("ยังไม่มีการเยี่ยมบ้าน","No home visits recorded."))

    with tab_refs:
        if refs:
            STATUS_TH = {"pending":"รอดำเนินการ","in_progress":"กำลังดำเนินการ","completed":"เสร็จสิ้น","cancelled":"ยกเลิก"}
            TARGET_TH = {"hospital":"โรงพยาบาล","health_center":"รพ.สต.","municipality":"เทศบาล","ngo":"มูลนิธิ"}
            for r in refs:
                icon = {"completed":"✅","in_progress":"🔵","pending":"🟡","cancelled":"⚫"}.get(r[3],"⚪")
                s = STATUS_TH.get(r[3],r[3]) if _t("th","en")=="th" else r[3]
                with st.expander(f"{icon} {fmt_date(r[0])} — {r[2] or TARGET_TH.get(r[1],r[1])} — {s}"):
                    if r[4]: st.markdown(f"**{_t('เหตุผล','Reason')}:** {r[4]}")
                    if r[5]: st.markdown(f"**{_t('ผลลัพธ์','Outcome')}:** {r[5]}")
        else:
            st.info(_t("ยังไม่มีการส่งต่อ","No referrals recorded."))

    with tab_assess:
        if assessments:
            import pandas as pd
            df = pd.DataFrame([{
                _t("วันที่ (พ.ศ.)","Date (BE)"):      fmt_date(a[0]),
                _t("ส่วนสูง","Height"):  f"{a[1]:.1f} cm" if a[1] else "—",
                _t("น้ำหนัก","Weight"):  f"{a[2]:.1f} kg" if a[2] else "—",
                "BMI":                    f"{a[3]:.1f}" if a[3] else "—",
                _t("ความดัน","BP"):       f"{int(a[4])}/{int(a[5])}" if a[4] and a[5] else "—",
                _t("ชีพจร","Pulse"):      f"{int(a[6])}" if a[6] else "—",
            } for a in assessments])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info(_t("ยังไม่มีการประเมินสุขภาพ","No health assessments recorded."))

    with tab_alerts:
        if alerts:
            SEV_ICON = {"critical":"🔴","high":"🟠","medium":"🟡","low":"🟢"}
            SEV_TH   = {"critical":"วิกฤต","high":"สูง","medium":"ปานกลาง","low":"ต่ำ"}
            for a in alerts:
                sev = SEV_TH.get(a[1],a[1]) if _t("th","en")=="th" else a[1]
                icon = SEV_ICON.get(a[1],"⚪")
                st.markdown(f"{icon} **{a[0]}** — {sev}  `{a[2]}`  _{fmt_date(a[3])}_")
        else:
            st.info(_t("ไม่มีการแจ้งเตือน","No alerts."))

    with tab_outcomes:
        if outcomes:
            OT_TH = {"improved":"ดีขึ้น","stable":"คงที่","deteriorated":"แย่ลง","resolved":"หายแล้ว","ongoing":"ต่อเนื่อง"}
            for o in outcomes:
                ot = OT_TH.get(o[0],o[0]) if _t("th","en")=="th" else o[0]
                with st.expander(f"📊 {fmt_date(o[1])} — {ot}"):
                    if o[2]: st.markdown(f"**{_t('ค่าเริ่มต้น','Baseline')}:** {o[2]}")
                    if o[3]: st.markdown(f"**{_t('ค่าปัจจุบัน','Current')}:** {o[3]}")
        else:
            st.info(_t("ยังไม่มีผลลัพธ์","No outcomes recorded."))
