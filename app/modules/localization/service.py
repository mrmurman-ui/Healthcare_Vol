"""
Localization service.  All UI labels live here — no hardcoded strings in pages.
Default language: Thai.
"""
from __future__ import annotations

import streamlit as st

TRANSLATIONS: dict[str, dict[str, str]] = {
    "th": {
        # Nav
        "nav_dashboard": "แดชบอร์ด",
        "nav_volunteers": "อาสาสมัคร",
        "nav_households": "ครัวเรือน",
        "nav_citizens": "ประชาชน",
        "nav_home_visits": "การเยี่ยมบ้าน",
        "nav_referrals": "การส่งต่อ",
        "nav_gis": "แผนที่ชุมชน",
        "nav_reports": "รายงาน",
        "nav_users": "ผู้ใช้งาน",
        "nav_audit": "บันทึกการตรวจสอบ",
        "nav_logout": "ออกจากระบบ",
        # Auth
        "login_title": "เข้าสู่ระบบ",
        "login_email": "อีเมล",
        "login_password": "รหัสผ่าน",
        "login_button": "เข้าสู่ระบบ",
        "login_error": "อีเมลหรือรหัสผ่านไม่ถูกต้อง",
        # Common
        "save": "บันทึก",
        "cancel": "ยกเลิก",
        "edit": "แก้ไข",
        "delete": "ลบ",
        "search": "ค้นหา",
        "add": "เพิ่ม",
        "export_pdf": "ส่งออก PDF",
        "export_excel": "ส่งออก Excel",
        "total": "ทั้งหมด",
        "active": "ใช้งาน",
        "inactive": "ไม่ใช้งาน",
        "status": "สถานะ",
        "name": "ชื่อ-นามสกุล",
        "phone": "เบอร์โทรศัพท์",
        "email": "อีเมล",
        "province": "จังหวัด",
        "district": "อำเภอ",
        "subdistrict": "ตำบล",
        "village": "หมู่บ้าน",
        "address": "ที่อยู่",
        "date": "วันที่",
        "action": "การดำเนินการ",
        # Dashboard
        "dash_volunteers": "อาสาสมัคร",
        "dash_households": "ครัวเรือน",
        "dash_citizens": "ประชาชน",
        "dash_visits": "การเยี่ยมบ้าน",
        "dash_referrals": "การส่งต่อ",
        # Volunteer
        "vol_code": "รหัสอาสาสมัคร",
        "vol_position": "ตำแหน่ง",
        "vol_photo": "รูปภาพ",
        # Household
        "hh_code": "รหัสครัวเรือน",
        "hh_head": "หัวหน้าครัวเรือน",
        "hh_income": "กลุ่มรายได้",
        "hh_housing": "ประเภทที่อยู่อาศัย",
        "hh_community": "ชุมชน",
        # Citizen
        "cit_dob": "วันเกิด",
        "cit_gender": "เพศ",
        "cit_occupation": "อาชีพ",
        "cit_education": "การศึกษา",
        "cit_elderly": "ผู้สูงอายุ",
        "cit_disabled": "ผู้พิการ",
        "cit_bedridden": "ติดเตียง",
        "cit_pregnant": "ตั้งครรภ์",
        "cit_alone": "อยู่คนเดียว",
        # Visit
        "vis_type": "ประเภทการเยี่ยม",
        "vis_observation": "การสังเกต",
        "vis_recommendation": "คำแนะนำ",
        "vis_volunteer": "อาสาสมัครผู้เยี่ยม",
        # Referral
        "ref_target": "ส่งต่อไปยัง",
        "ref_status": "สถานะ",
        "ref_outcome": "ผลลัพธ์",
        "ref_followup": "การติดตาม",
        # Reports
        "rep_vol": "รายงานอาสาสมัคร",
        "rep_hh": "รายงานครัวเรือน",
        "rep_cit": "รายงานประชาชน",
        "rep_vis": "รายงานการเยี่ยมบ้าน",
        "rep_ref": "รายงานการส่งต่อ",
    },
    "en": {
        "nav_dashboard": "Dashboard",
        "nav_volunteers": "Volunteers",
        "nav_households": "Households",
        "nav_citizens": "Citizens",
        "nav_home_visits": "Home Visits",
        "nav_referrals": "Referrals",
        "nav_gis": "Community Map",
        "nav_reports": "Reports",
        "nav_users": "Users",
        "nav_audit": "Audit Log",
        "nav_logout": "Logout",
        "login_title": "Login",
        "login_email": "Email",
        "login_password": "Password",
        "login_button": "Sign In",
        "login_error": "Invalid email or password",
        "save": "Save",
        "cancel": "Cancel",
        "edit": "Edit",
        "delete": "Delete",
        "search": "Search",
        "add": "Add",
        "export_pdf": "Export PDF",
        "export_excel": "Export Excel",
        "total": "Total",
        "active": "Active",
        "inactive": "Inactive",
        "status": "Status",
        "name": "Name",
        "phone": "Phone",
        "email": "Email",
        "province": "Province",
        "district": "District",
        "subdistrict": "Subdistrict",
        "village": "Village",
        "address": "Address",
        "date": "Date",
        "action": "Action",
        "dash_volunteers": "Volunteers",
        "dash_households": "Households",
        "dash_citizens": "Citizens",
        "dash_visits": "Home Visits",
        "dash_referrals": "Referrals",
        "vol_code": "Volunteer Code",
        "vol_position": "Position",
        "vol_photo": "Photo",
        "hh_code": "Household Code",
        "hh_head": "Head of Household",
        "hh_income": "Income Group",
        "hh_housing": "Housing Type",
        "hh_community": "Community",
        "cit_dob": "Date of Birth",
        "cit_gender": "Gender",
        "cit_occupation": "Occupation",
        "cit_education": "Education",
        "cit_elderly": "Elderly",
        "cit_disabled": "Disabled",
        "cit_bedridden": "Bedridden",
        "cit_pregnant": "Pregnant",
        "cit_alone": "Living Alone",
        "vis_type": "Visit Type",
        "vis_observation": "Observation",
        "vis_recommendation": "Recommendation",
        "vis_volunteer": "Visiting Volunteer",
        "ref_target": "Referred To",
        "ref_status": "Status",
        "ref_outcome": "Outcome",
        "ref_followup": "Follow-up",
        "rep_vol": "Volunteer Report",
        "rep_hh": "Household Report",
        "rep_cit": "Citizen Report",
        "rep_vis": "Home Visit Report",
        "rep_ref": "Referral Report",
    },
}


def get_locale() -> str:
    return st.session_state.get("locale", "th")


def t(key: str) -> str:
    """Translate a key to the current locale, fallback to English, fallback to key."""
    locale = get_locale()
    return (
        TRANSLATIONS.get(locale, {}).get(key)
        or TRANSLATIONS["en"].get(key)
        or key
    )


def set_locale(locale: str) -> None:
    st.session_state["locale"] = locale


# ── V2 additions (injected at module load) ────────────────────────────────────
_V2_TH = {
    "nav_tasks": "การจัดการงาน",
    "nav_followups": "การติดตาม",
    "nav_notifications": "การแจ้งเตือน",
    "nav_announcements": "ประกาศ",
    "nav_projects": "โครงการชุมชน",
    "nav_analytics": "วิเคราะห์ข้อมูล",
    "nav_ai_assistant": "ผู้ช่วย AI",
    "task_title": "ชื่องาน",
    "task_type": "ประเภทงาน",
    "task_priority": "ความสำคัญ",
    "task_status": "สถานะ",
    "task_due": "กำหนดส่ง",
    "task_assigned": "มอบหมายให้",
    "followup_type": "ประเภทการติดตาม",
    "project_name": "ชื่อโครงการ",
    "project_type": "ประเภทโครงการ",
    "project_budget": "งบประมาณ",
    "project_owner": "เจ้าของโครงการ",
    "ann_type": "ประเภทประกาศ",
    "ann_target": "พื้นที่เป้าหมาย",
}

_V2_EN = {
    "nav_tasks": "Tasks",
    "nav_followups": "Follow-Ups",
    "nav_notifications": "Notifications",
    "nav_announcements": "Announcements",
    "nav_projects": "Community Projects",
    "nav_analytics": "Analytics",
    "nav_ai_assistant": "AI Assistant",
    "task_title": "Task Title",
    "task_type": "Task Type",
    "task_priority": "Priority",
    "task_status": "Status",
    "task_due": "Due Date",
    "task_assigned": "Assigned To",
    "followup_type": "Follow-Up Type",
    "project_name": "Project Name",
    "project_type": "Project Type",
    "project_budget": "Budget",
    "project_owner": "Project Owner",
    "ann_type": "Announcement Type",
    "ann_target": "Target Area",
}

TRANSLATIONS["th"].update(_V2_TH)
TRANSLATIONS["en"].update(_V2_EN)


# ── V2.51 additions ───────────────────────────────────────────────────────────
_V251_TH = {
    "nav_health_profiles": "โปรไฟล์สุขภาพ",
    "nav_health_assessments": "การประเมินสุขภาพ",
    "nav_health_trends": "แนวโน้มสุขภาพ",
    "nav_elderly_monitoring": "ติดตามผู้สูงอายุ",
    "nav_early_warning": "ระบบเตือนภัย",
    "nav_cvi": "ดัชนีความเปราะบาง",
    "nav_community_health": "สุขภาพชุมชน",
    "nav_health_analytics": "วิเคราะห์สุขภาพ",
    "cvi_score": "คะแนน CVI",
    "cvi_category": "ระดับ CVI",
    "alert_severity": "ระดับการเตือน",
    "chronic_conditions": "โรคเรื้อรัง (รายงานตนเอง)",
    "functional_status": "สถานะการทำงาน",
    "social_health": "สุขภาพทางสังคม",
    "home_environment": "สภาพแวดล้อมบ้าน",
    "service_needs": "ความต้องการบริการ",
}
_V251_EN = {
    "nav_health_profiles": "Health Profiles",
    "nav_health_assessments": "Health Assessments",
    "nav_health_trends": "Health Trends",
    "nav_elderly_monitoring": "Elderly Monitoring",
    "nav_early_warning": "Early Warning",
    "nav_cvi": "Vulnerability Index",
    "nav_community_health": "Community Health",
    "nav_health_analytics": "Health Analytics",
    "cvi_score": "CVI Score",
    "cvi_category": "CVI Category",
    "alert_severity": "Alert Severity",
    "chronic_conditions": "Chronic Conditions (self-reported)",
    "functional_status": "Functional Status",
    "social_health": "Social Health",
    "home_environment": "Home Environment",
    "service_needs": "Service Needs",
}
TRANSLATIONS["th"].update(_V251_TH)
TRANSLATIONS["en"].update(_V251_EN)


# ── V2.53 additions ───────────────────────────────────────────────────────────
_V253_TH = {
    "nav_quality_management": "การจัดการคุณภาพ",
    "nav_population_health": "สุขภาพประชากร",
    "nav_outcomes": "ผลลัพธ์กรณีศึกษา",
    "nav_risk_stratification": "การจัดลำดับความเสี่ยง",
    "nav_capacity_planning": "การวางแผนกำลังคน",
    "nav_performance": "การบริหารผลการปฏิบัติ",
    "nav_scorecards": "คะแนนชุมชน",
    "nav_executive": "ศูนย์บัญชาการผู้บริหาร",
}
_V253_EN = {
    "nav_quality_management": "Quality Management",
    "nav_population_health": "Population Health",
    "nav_outcomes": "Case Outcomes",
    "nav_risk_stratification": "Risk Stratification",
    "nav_capacity_planning": "Capacity Planning",
    "nav_performance": "Performance Management",
    "nav_scorecards": "Community Scorecards",
    "nav_executive": "Executive Command Center",
}
TRANSLATIONS["th"].update(_V253_TH)
TRANSLATIONS["en"].update(_V253_EN)


# ── V2.54 additions ───────────────────────────────────────────────────────────
_V254_TH = {
    "nav_settings": "การตั้งค่าระบบ",
    "nav_feature_flags": "ฟีเจอร์แฟล็ก",
    "nav_system_health": "สุขภาพระบบ",
    "nav_error_tracking": "ติดตามข้อผิดพลาด",
    "nav_app_logs": "บันทึกแอปพลิเคชัน",
    "nav_database_tools": "เครื่องมือฐานข้อมูล",
    "nav_backup": "สำรองข้อมูล",
    "nav_scheduler": "ตัวจัดการงาน",
    "nav_import": "นำเข้าข้อมูล",
    "nav_versioning": "เวอร์ชันระบบ",
}
_V254_EN = {
    "nav_settings": "System Settings",
    "nav_feature_flags": "Feature Flags",
    "nav_system_health": "System Health",
    "nav_error_tracking": "Error Tracking",
    "nav_app_logs": "Application Logs",
    "nav_database_tools": "Database Tools",
    "nav_backup": "Backup & Restore",
    "nav_scheduler": "Job Scheduler",
    "nav_import": "Import Engine",
    "nav_versioning": "System Version",
}
TRANSLATIONS["th"].update(_V254_TH)
TRANSLATIONS["en"].update(_V254_EN)


# V2.54.1 additions
_V2541_TH = {
    "nav_user_management": "จัดการผู้ใช้",
    "nav_roles": "บทบาทและสิทธิ์",
    "nav_security": "แดชบอร์ดความปลอดภัย",
    "nav_login_history": "ประวัติการเข้าใช้",
    "user_status": "สถานะผู้ใช้",
    "user_role": "บทบาท",
    "user_scope": "พื้นที่รับผิดชอบ",
    "create_user": "สร้างผู้ใช้",
    "reset_password": "รีเซ็ตรหัสผ่าน",
    "deactivate": "ปิดใช้งาน",
    "reactivate": "เปิดใช้งาน",
}
_V2541_EN = {
    "nav_user_management": "User Management",
    "nav_roles": "Roles & Permissions",
    "nav_security": "Security Dashboard",
    "nav_login_history": "Login History",
    "user_status": "User Status",
    "user_role": "Role",
    "user_scope": "Area Scope",
    "create_user": "Create User",
    "reset_password": "Reset Password",
    "deactivate": "Deactivate",
    "reactivate": "Reactivate",
}
TRANSLATIONS["th"].update(_V2541_TH)
TRANSLATIONS["en"].update(_V2541_EN)


# V2.54.2B additions
_V2542B_TH = {
    "nav_executive_v2": "ศูนย์บัญชาการอัจฉริยะ",
    "nav_analytics_v2": "วิเคราะห์ข้อมูลขั้นสูง",
}
_V2542B_EN = {
    "nav_executive_v2": "Executive Intelligence",
    "nav_analytics_v2": "Advanced Analytics",
}
TRANSLATIONS["th"].update(_V2542B_TH)
TRANSLATIONS["en"].update(_V2542B_EN)


# ── Additional nav keys ───────────────────────────────────────────────────────
_EXTRA_TH = {
    "nav_community_projects": "โครงการชุมชน",
    "nav_campaigns":          "แคมเปญสุขภาพ",
    "nav_health_assessments": "การประเมินสุขภาพ",
    "nav_health_profiles":    "โปรไฟล์สุขภาพ",
    "nav_risk_stratification":"การจัดลำดับความเสี่ยง",
    "nav_outcomes":           "ผลลัพธ์กรณีศึกษา",
    "nav_performance":        "การบริหารผลการปฏิบัติงาน",
    "nav_scorecards":         "คะแนนชุมชน",
    "nav_ai_assistant":       "ผู้ช่วย AI",
    "nav_reports":            "รายงาน",
}
_EXTRA_EN = {
    "nav_community_projects": "Community Projects",
    "nav_campaigns":          "Health Campaigns",
    "nav_health_assessments": "Health Assessments",
    "nav_health_profiles":    "Health Profiles",
    "nav_risk_stratification":"Risk Stratification",
    "nav_outcomes":           "Case Outcomes",
    "nav_performance":        "Performance Management",
    "nav_scorecards":         "Community Scorecards",
    "nav_ai_assistant":       "AI Assistant",
    "nav_reports":            "Reports",
}
TRANSLATIONS["th"].update(_EXTRA_TH)
TRANSLATIONS["en"].update(_EXTRA_EN)
