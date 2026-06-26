"""Reports — PDF / Excel / HTML export for all report types."""
from __future__ import annotations
from datetime import date

import streamlit as st
from sqlalchemy import select, text

from app.core.db_sync import get_sync_db
from app.modules.localization.service import t
from app.modules.reports.service import generate_excel, generate_pdf
from app.shared.date_utils import fmt_date, ad_to_be_year


def _t(th: str, en: str) -> str:
    return th if st.session_state.get("lang", "TH") == "TH" else en


# ── Report definitions (key → Thai label / EN label / loader) ────────────────
REPORTS = [
    ("volunteers",   "รายงานอาสาสมัคร",        "Volunteer Report"),
    ("households",   "รายงานครัวเรือน",         "Household Report"),
    ("citizens",     "รายงานประชาชน",           "Citizen Report"),
    ("elderly",      "รายงานผู้สูงอายุ",         "Elderly Report"),
    ("home_visits",  "รายงานการเยี่ยมบ้าน",      "Home Visit Report"),
    ("referrals",    "รายงานการส่งต่อ",          "Referral Report"),
    ("tasks",        "รายงานการจัดการงาน",       "Task Report"),
    ("assessments",  "รายงานการประเมินสุขภาพ",   "Health Assessment Report"),
    ("campaigns",    "รายงานแคมเปญสุขภาพ",       "Campaign Report"),
    ("projects",     "รายงานโครงการชุมชน",       "Community Project Report"),
]


def _load_data(report_key: str) -> tuple[str, list[str], list[list]]:
    """Load headers and rows for the selected report type."""
    is_th = st.session_state.get("lang", "TH") == "TH"

    with get_sync_db() as db:

        # ── Volunteers ────────────────────────────────────────────────────────
        if report_key == "volunteers":
            title = _t("รายงานอาสาสมัครสาธารณสุข", "Volunteer Report")
            headers = [_t("รหัส อสม.","Code"), _t("ชื่อ-นามสกุล","Name"),
                       _t("ตำแหน่ง","Position"), _t("จังหวัด","Province"),
                       _t("อำเภอ","District"), _t("ตำบล","Subdistrict"),
                       _t("โทรศัพท์","Phone"), _t("สถานะ","Status")]
            rows_raw = db.execute(text("""
                SELECT volunteer_code, full_name, position, province,
                       district, subdistrict, phone, status
                FROM volunteers ORDER BY full_name
            """)).fetchall()
            STATUS_TH = {"active":"ใช้งาน","inactive":"ไม่ใช้งาน"}
            rows = [[r[0] or "", r[1] or "", r[2] or "", r[3] or "",
                     r[4] or "", r[5] or "", r[6] or "",
                     STATUS_TH.get(r[7] or "", r[7] or "") if is_th else (r[7] or "")]
                    for r in rows_raw]

        # ── Households ────────────────────────────────────────────────────────
        elif report_key == "households":
            title = _t("รายงานครัวเรือน", "Household Report")
            headers = [_t("รหัสครัวเรือน","Code"), _t("หัวหน้าครัวเรือน","Head"),
                       _t("ที่อยู่","Address"), _t("หมู่บ้าน","Village"),
                       _t("อำเภอ","District"), _t("จังหวัด","Province"),
                       _t("โทรศัพท์","Phone"), _t("กลุ่มรายได้","Income")]
            INCOME_TH = {"very_low":"รายได้น้อยมาก","low":"รายได้น้อย",
                         "medium":"รายได้ปานกลาง","high":"รายได้สูง"}
            rows_raw = db.execute(text("""
                SELECT household_code, head_of_household, address, village,
                       district, province, phone, income_group
                FROM households ORDER BY household_code
            """)).fetchall()
            rows = [[r[0] or "", r[1] or "", r[2] or "", r[3] or "",
                     r[4] or "", r[5] or "", r[6] or "",
                     INCOME_TH.get(r[7] or "", r[7] or "") if is_th else (r[7] or "")]
                    for r in rows_raw]

        # ── Citizens ──────────────────────────────────────────────────────────
        elif report_key == "citizens":
            title = _t("รายงานประชาชน", "Citizen Report")
            headers = [_t("รหัส","Code"), _t("ชื่อ-นามสกุล","Name"),
                       _t("เพศ","Gender"), _t("วันเกิด","DOB"),
                       _t("อายุ (ปี)","Age"), _t("โทรศัพท์","Phone"),
                       _t("อาชีพ","Occupation"),
                       _t("ผู้สูงอายุ","Elderly"), _t("ผู้พิการ","Disabled"),
                       _t("ติดเตียง","Bedridden")]
            GENDER_TH = {"male":"ชาย","female":"หญิง","other":"อื่นๆ"}
            rows_raw = db.execute(text("""
                SELECT citizen_code, full_name, gender, date_of_birth,
                       phone, occupation, is_elderly, is_disabled, is_bedridden
                FROM citizens
                WHERE is_deleted IS NULL OR is_deleted=false
                ORDER BY full_name
            """)).fetchall()
            def _age(dob):
                if not dob: return ""
                try:
                    from datetime import datetime
                    born = dob if hasattr(dob,"year") else datetime.strptime(str(dob)[:10],"%Y-%m-%d").date()
                    t2 = date.today()
                    return str(t2.year-born.year-((t2.month,t2.day)<(born.month,born.day)))
                except: return ""
            rows = [[r[0] or "", r[1] or "",
                     GENDER_TH.get(r[2] or "", r[2] or "") if is_th else (r[2] or ""),
                     fmt_date(r[3]), _age(r[3]),
                     r[4] or "", r[5] or "",
                     _t("ใช่","Yes") if r[6] else "",
                     _t("ใช่","Yes") if r[7] else "",
                     _t("ใช่","Yes") if r[8] else ""]
                    for r in rows_raw]

        # ── Elderly ───────────────────────────────────────────────────────────
        elif report_key == "elderly":
            title = _t("รายงานผู้สูงอายุ", "Elderly Citizen Report")
            headers = [_t("รหัส","Code"), _t("ชื่อ-นามสกุล","Name"),
                       _t("เพศ","Gender"), _t("วันเกิด","DOB"),
                       _t("อายุ (ปี)","Age"), _t("โทรศัพท์","Phone"),
                       _t("ติดเตียง","Bedridden"), _t("ผู้พิการ","Disabled"),
                       _t("ตั้งครรภ์","Pregnant"), _t("อยู่คนเดียว","Alone"),
                       _t("หมู่บ้าน","Village"), _t("อำเภอ","District")]
            GENDER_TH = {"male":"ชาย","female":"หญิง","other":"อื่นๆ"}
            rows_raw = db.execute(text("""
                SELECT citizen_code, full_name, gender, date_of_birth,
                       phone, is_bedridden, is_disabled, is_pregnant,
                       is_living_alone,
                       COALESCE(village,'') as village,
                       COALESCE(district,'') as district
                FROM citizens
                WHERE is_elderly=true AND (is_deleted IS NULL OR is_deleted=false)
                ORDER BY full_name
            """)).fetchall()
            def _age2(dob):
                if not dob: return ""
                try:
                    from datetime import datetime
                    born = dob if hasattr(dob,"year") else datetime.strptime(str(dob)[:10],"%Y-%m-%d").date()
                    t2 = date.today()
                    return str(t2.year-born.year-((t2.month,t2.day)<(born.month,born.day)))
                except: return ""
            yn = lambda v: (_t("ใช่","Yes") if v else "")
            rows = [[r[0] or "", r[1] or "",
                     GENDER_TH.get(r[2] or "", r[2] or "") if is_th else (r[2] or ""),
                     fmt_date(r[3]), _age2(r[3]),
                     r[4] or "", yn(r[5]), yn(r[6]), yn(r[7]), yn(r[8]),
                     r[9] or "", r[10] or ""]
                    for r in rows_raw]

        # ── Home Visits ───────────────────────────────────────────────────────
        elif report_key == "home_visits":
            title = _t("รายงานการเยี่ยมบ้าน", "Home Visit Report")
            headers = [_t("วันที่","Date"), _t("ประชาชน","Citizen"),
                       _t("อาสาสมัคร","Volunteer"), _t("ประเภท","Type"),
                       _t("การสังเกต","Observation"), _t("คำแนะนำ","Recommendation")]
            VTYPE_TH = {"routine":"ตามแผน","follow_up":"ติดตาม",
                        "emergency":"ฉุกเฉิน","post_referral":"หลังส่งต่อ"}
            rows_raw = db.execute(text("""
                SELECT hv.visit_date, c.full_name, v.full_name,
                       hv.visit_type, hv.observation, hv.recommendation
                FROM home_visits hv
                LEFT JOIN citizens c ON c.id=hv.citizen_id
                LEFT JOIN volunteers v ON v.id=hv.volunteer_id
                ORDER BY hv.visit_date DESC LIMIT 2000
            """)).fetchall()
            rows = [[fmt_date(r[0]), r[1] or "", r[2] or "",
                     VTYPE_TH.get(r[3] or "", r[3] or "") if is_th else (r[3] or ""),
                     (r[4] or "")[:100], (r[5] or "")[:100]]
                    for r in rows_raw]

        # ── Referrals ─────────────────────────────────────────────────────────
        elif report_key == "referrals":
            title = _t("รายงานการส่งต่อ", "Referral Report")
            headers = [_t("วันที่","Date"), _t("ประชาชน","Citizen"),
                       _t("จุดหมาย","Target"), _t("หน่วยงาน","Facility"),
                       _t("เหตุผล","Reason"), _t("สถานะ","Status"),
                       _t("ผลลัพธ์","Outcome")]
            STATUS_TH = {"pending":"รอดำเนินการ","in_progress":"กำลังดำเนินการ",
                         "completed":"เสร็จสิ้น","cancelled":"ยกเลิก"}
            TARGET_TH = {"hospital":"โรงพยาบาล","health_center":"รพ.สต.",
                         "municipality":"เทศบาล","ngo":"มูลนิธิ"}
            rows_raw = db.execute(text("""
                SELECT r.referral_date, c.full_name, r.target,
                       r.target_name, r.reason, r.status, r.outcome
                FROM referrals r
                LEFT JOIN citizens c ON c.id=r.citizen_id
                ORDER BY r.referral_date DESC LIMIT 2000
            """)).fetchall()
            rows = [[fmt_date(r[0]), r[1] or "",
                     TARGET_TH.get(r[2] or "", r[2] or "") if is_th else (r[2] or ""),
                     r[3] or "", (r[4] or "")[:80],
                     STATUS_TH.get(r[5] or "", r[5] or "") if is_th else (r[5] or ""),
                     (r[6] or "")[:80]]
                    for r in rows_raw]

        # ── Tasks ─────────────────────────────────────────────────────────────
        elif report_key == "tasks":
            title = _t("รายงานการจัดการงาน", "Task Management Report")
            headers = [_t("รหัสงาน","Code"), _t("ชื่องาน","Title"),
                       _t("ประเภท","Type"), _t("ระดับความสำคัญ","Priority"),
                       _t("สถานะ","Status"), _t("วันกำหนดส่ง","Due Date"),
                       _t("ผู้รับผิดชอบ","Assigned To")]
            PRIO_TH = {"low":"ต่ำ","medium":"ปานกลาง","high":"สูง","critical":"วิกฤต"}
            STAT_TH = {"new":"ใหม่","assigned":"มอบหมาย","in_progress":"กำลังดำเนิน",
                       "completed":"เสร็จสิ้น","cancelled":"ยกเลิก","overdue":"เกินกำหนด"}
            rows_raw = db.execute(text("""
                SELECT task_code, title, task_type, priority, status,
                       due_date, assigned_to
                FROM tasks WHERE is_deleted=false ORDER BY due_date
            """)).fetchall()
            rows = [[r[0] or "", r[1] or "", r[2] or "",
                     PRIO_TH.get(r[3] or "", r[3] or "") if is_th else (r[3] or ""),
                     STAT_TH.get(r[4] or "", r[4] or "") if is_th else (r[4] or ""),
                     fmt_date(r[5]), r[6] or ""]
                    for r in rows_raw]

        # ── Health Assessments ────────────────────────────────────────────────
        elif report_key == "assessments":
            title = _t("รายงานการประเมินสุขภาพ", "Health Assessment Report")
            headers = [_t("วันที่","Date"), _t("ประชาชน","Citizen"),
                       _t("ส่วนสูง (cm)","Height (cm)"), _t("น้ำหนัก (kg)","Weight (kg)"),
                       _t("BMI","BMI"), _t("ความดัน (mmHg)","BP (mmHg)"),
                       _t("ชีพจร","Pulse"), _t("อุณหภูมิ (°C)","Temp (°C)")]
            rows_raw = db.execute(text("""
                SELECT ha.assessment_date, c.full_name,
                       ha.height_cm, ha.weight_kg, ha.bmi,
                       ha.bp_systolic, ha.bp_diastolic, ha.pulse_rate, ha.temperature_c
                FROM health_assessments ha
                LEFT JOIN citizens c ON c.id=ha.citizen_id
                WHERE ha.is_deleted IS NULL OR ha.is_deleted=false
                ORDER BY ha.assessment_date DESC LIMIT 2000
            """)).fetchall()
            rows = [[fmt_date(r[0]), r[1] or "",
                     f"{r[2]:.1f}" if r[2] else "",
                     f"{r[3]:.1f}" if r[3] else "",
                     f"{r[4]:.1f}" if r[4] else "",
                     f"{int(r[5])}/{int(r[6])}" if r[5] and r[6] else "",
                     f"{int(r[7])}" if r[7] else "",
                     f"{r[8]:.1f}" if r[8] else ""]
                    for r in rows_raw]

        # ── Campaigns ─────────────────────────────────────────────────────────
        elif report_key == "campaigns":
            title = _t("รายงานแคมเปญสุขภาพ", "Health Campaign Report")
            headers = [_t("รหัส","Code"), _t("ชื่อแคมเปญ","Campaign Name"),
                       _t("ประเภท","Type"), _t("กลุ่มเป้าหมาย","Target Group"),
                       _t("สถานะ","Status"), _t("วันเริ่ม","Start"),
                       _t("วันสิ้นสุด","End"), _t("เป้าหมาย","Target"),
                       _t("จริง","Actual"), _t("งบประมาณ","Budget")]
            TYPE_TH = {"health_screening":"ตรวจสุขภาพ","vaccination":"ฉีดวัคซีน",
                       "health_education":"ให้ความรู้","disease_prevention":"ป้องกันโรค",
                       "elderly_care":"ดูแลผู้สูงอายุ","mental_health":"สุขภาพจิต",
                       "nutrition":"โภชนาการ","exercise":"ออกกำลังกาย"}
            STAT_TH = {"planning":"วางแผน","active":"กำลังดำเนิน",
                       "completed":"เสร็จสิ้น","cancelled":"ยกเลิก"}
            TG_TH = {"all":"ทุกกลุ่ม","elderly":"ผู้สูงอายุ","children":"เด็ก",
                     "pregnant":"หญิงตั้งครรภ์","chronic_disease":"โรคเรื้อรัง"}
            rows_raw = db.execute(text("""
                SELECT campaign_code, campaign_name, campaign_type, target_group,
                       status, start_date, end_date, target_count, actual_count, budget
                FROM health_campaigns
                WHERE is_deleted=false ORDER BY start_date DESC
            """)).fetchall()
            rows = [[r[0] or "", r[1] or "",
                     TYPE_TH.get(r[2] or "", r[2] or "") if is_th else (r[2] or ""),
                     TG_TH.get(r[3] or "", r[3] or "") if is_th else (r[3] or ""),
                     STAT_TH.get(r[4] or "", r[4] or "") if is_th else (r[4] or ""),
                     fmt_date(r[5]), fmt_date(r[6]),
                     str(r[7] or ""), str(r[8] or ""),
                     f"฿{float(r[9]):,.0f}" if r[9] else ""]
                    for r in rows_raw]

        # ── Community Projects ────────────────────────────────────────────────
        elif report_key == "projects":
            title = _t("รายงานโครงการชุมชน", "Community Project Report")
            headers = [_t("รหัส","Code"), _t("ชื่อโครงการ","Project Name"),
                       _t("ประเภท","Type"), _t("สถานะ","Status"),
                       _t("วันเริ่ม","Start"), _t("วันสิ้นสุด","End"),
                       _t("งบประมาณ","Budget"), _t("ผู้รับผิดชอบ","Owner"),
                       _t("อำเภอ","District")]
            TYPE_TH = {"elderly_club":"ชมรมผู้สูงอายุ","exercise_program":"ออกกำลังกาย",
                       "home_modification":"ปรับปรุงบ้าน","community_survey":"สำรวจชุมชน",
                       "health_activity":"กิจกรรมสุขภาพ","other":"อื่นๆ"}
            STAT_TH = {"planning":"วางแผน","active":"กำลังดำเนิน",
                       "completed":"เสร็จสิ้น","cancelled":"ยกเลิก"}
            rows_raw = db.execute(text("""
                SELECT project_code, project_name, project_type, status,
                       start_date, end_date, budget, owner, district
                FROM community_projects
                WHERE is_deleted=false ORDER BY start_date DESC
            """)).fetchall()
            rows = [[r[0] or "", r[1] or "",
                     TYPE_TH.get(r[2] or "", r[2] or "") if is_th else (r[2] or ""),
                     STAT_TH.get(r[3] or "", r[3] or "") if is_th else (r[3] or ""),
                     fmt_date(r[4]), fmt_date(r[5]),
                     f"฿{float(r[6]):,.0f}" if r[6] else "",
                     r[7] or "", r[8] or ""]
                    for r in rows_raw]

        else:
            title, headers, rows = "Report", [], []

    return title, headers, rows


def render_reports() -> None:
    st.header(t("nav_reports"))
    is_th = st.session_state.get("lang", "TH") == "TH"

    # Build display names and key mapping
    report_display = [r[1] if is_th else r[2] for r in REPORTS]
    report_keys    = [r[0] for r in REPORTS]

    sel_idx = st.selectbox(
        _t("เลือกรายงาน", "Select Report"),
        range(len(report_display)),
        format_func=lambda i: report_display[i],
        key="report_type_sel"
    )
    report_key   = report_keys[sel_idx]
    report_label = report_display[sel_idx]

    # Date range filter
    with st.expander("📅 " + _t("กรองตามวันที่ (ไม่บังคับ)", "Date Range Filter (optional)")):
        dc1, dc2 = st.columns(2)
        from app.shared.date_utils import be_date_input_col
        from datetime import timedelta
        d_from = be_date_input_col(dc1, _t("จากวันที่","From Date"),
                                   value=date.today()-timedelta(days=365),
                                   key="rpt_from")
        d_to   = be_date_input_col(dc2, _t("ถึงวันที่","To Date"),
                                   value=date.today(), key="rpt_to")

    col1, col2, col3 = st.columns(3)
    export_pdf   = col1.button("📄 " + _t("ส่งออก PDF","Export PDF"),
                                use_container_width=True, type="primary")
    export_excel = col2.button("📊 " + _t("ส่งออก Excel","Export Excel"),
                                use_container_width=True)
    preview_btn  = col3.button("👁️ " + _t("ดูตัวอย่าง","Preview"),
                                use_container_width=True)

    # Preview
    if preview_btn or st.session_state.get("rpt_previewing") == report_key:
        st.session_state["rpt_previewing"] = report_key
        with st.spinner(_t("กำลังโหลดข้อมูล...","Loading...")):
            try:
                title, headers, rows = _load_data(report_key)
            except Exception as e:
                st.error(f"❌ {e}"); return
        st.divider()
        st.markdown(f"**{title}** — {len(rows):,} {_t('รายการ','records')}")
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows, columns=headers)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         height=min(400, len(rows)*36+40))
        else:
            st.info(_t("ไม่มีข้อมูลสำหรับรายงานนี้","No data for this report."))

    # Export
    if export_pdf or export_excel:
        with st.spinner(_t("กำลังสร้างรายงาน...","Generating report...")):
            try:
                title, headers, rows = _load_data(report_key)
            except Exception as e:
                st.error(f"❌ {e}"); return

        if not rows:
            st.warning(_t("ไม่มีข้อมูลสำหรับส่งออก","No data to export.")); return

        st.success(_t(f"✅ พบข้อมูล {len(rows):,} รายการ",
                      f"✅ Found {len(rows):,} records"))

        safe_name = report_key.replace(" ", "_")

        if export_pdf:
            data = generate_pdf(title, headers, rows)
            is_html = data[:5] == b"<!DOC"
            if is_html:
                st.warning(_t(
                    "⚠️ ไม่พบฟอนต์ภาษาไทย — ส่งออกเป็น HTML แทน PDF\n"
                    "ติดตั้งฟอนต์: https://www.f0nt.com/release/th-sarabun-new/",
                    "⚠️ Thai font not found — exported as HTML.\n"
                    "Install font: https://www.f0nt.com/release/th-sarabun-new/"
                ))
                st.download_button(
                    "⬇ " + _t("ดาวน์โหลด HTML","Download HTML"),
                    data, f"{safe_name}.html", "text/html; charset=utf-8"
                )
            else:
                st.download_button(
                    "⬇ " + _t("ดาวน์โหลด PDF","Download PDF"),
                    data, f"{safe_name}.pdf", "application/pdf"
                )

        if export_excel:
            data = generate_excel(title, headers, rows)
            st.download_button(
                "⬇ " + _t("ดาวน์โหลด Excel","Download Excel"),
                data, f"{safe_name}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
