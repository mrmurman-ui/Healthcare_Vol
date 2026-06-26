"""Role-based Navigation Service V2.60 — workflow-centric, not module-centric."""
from __future__ import annotations

from dataclasses import dataclass, field
from app.shared.enums import UserRole

# ── Page registry — all pages with workflow metadata ─────────────────────────
# key: (page_key, label, icon, group, roles_allowed)

@dataclass
class NavPage:
    key: str
    label: str
    label_th: str
    icon: str
    group: str
    roles: list[str]  # empty = all roles


ALL_PAGES: list[NavPage] = [
    # HOME group
    NavPage("dashboard",         "Dashboard",          "แดชบอร์ด",            "🏠", "HOME",     []),
    NavPage("tasks",             "My Tasks",           "งานของฉัน",           "✅", "HOME",     []),
    NavPage("notifications",     "Notifications",      "การแจ้งเตือน",        "🔔", "HOME",     []),
    NavPage("announcements",     "Announcements",      "ประกาศ",              "📢", "HOME",     []),
    NavPage("quick_actions",     "Quick Actions",      "ดำเนินการด่วน",       "⚡", "HOME",     []),
    NavPage("workspace",         "My Workspace",       "พื้นที่ทำงาน",         "🖥️", "HOME",     []),

    # PEOPLE group
    NavPage("citizens",          "Citizens",           "ประชาชน",             "👤", "PEOPLE",   []),
    NavPage("households",        "Households",         "ครัวเรือน",           "🏘️", "PEOPLE",   []),
    NavPage("volunteers",        "Volunteers",         "อาสาสมัคร",           "🦺", "PEOPLE",   []),
    NavPage("elderly_monitoring","Elderly",            "ผู้สูงอายุ",           "👴", "PEOPLE",   []),

    # CARE group
    NavPage("health_assessments","Assessments",        "การประเมินสุขภาพ",     "📏", "CARE",     []),
    NavPage("health_profiles",   "Health Profiles",    "โปรไฟล์สุขภาพ",       "🩺", "CARE",     []),
    NavPage("home_visits",       "Home Visits",        "การเยี่ยมบ้าน",        "🏠", "CARE",     []),
    NavPage("referrals",         "Referrals",          "การส่งต่อ",           "📤", "CARE",     []),
    NavPage("followups",         "Follow-Ups",         "การติดตาม",           "🔁", "CARE",     []),
    NavPage("health_trends",     "Health Trends",      "แนวโน้มสุขภาพ",       "📈", "CARE",     []),
    NavPage("early_warning",     "Early Warning",      "ระบบเตือนภัย",        "⚠️", "CARE",     []),
    NavPage("cvi",               "Vulnerability Index","ดัชนีความเปราะบาง",    "📊", "CARE",     []),

    # SERVICES group
    NavPage("projects",          "Community Projects", "โครงการชุมชน",        "🏗️", "SERVICES", []),
    NavPage("campaigns",         "Campaigns",          "แคมเปญ",              "📣", "SERVICES", []),
    NavPage("import_engine",     "Import Data",        "นำเข้าข้อมูล",        "📥", "SERVICES", ["super_admin","province_admin","district_admin"]),

    # MAPS group
    NavPage("gis",               "Community Map",      "แผนที่ชุมชน",         "🗺️", "MAPS",     []),

    # INSIGHTS group
    NavPage("executive_v2",      "Executive Intel",    "ศูนย์บัญชาการ",       "🎯", "INSIGHTS", []),
    NavPage("population_health", "Population Health",  "สุขภาพประชากร",       "🌏", "INSIGHTS", []),
    NavPage("health_analytics",  "Health Analytics",   "วิเคราะห์สุขภาพ",     "📊", "INSIGHTS", []),
    NavPage("analytics",         "Analytics",          "วิเคราะห์ข้อมูล",     "📉", "INSIGHTS", []),
    NavPage("risk_stratification","Risk Intel",        "การจัดลำดับความเสี่ยง","🎯", "INSIGHTS", []),
    NavPage("capacity_planning", "Capacity Planning",  "การวางแผนกำลังคน",    "📐", "INSIGHTS", []),
    NavPage("community_health",  "Community Health",   "สุขภาพชุมชน",         "🏘️", "INSIGHTS", []),
    NavPage("quality_management","Quality Mgmt",       "การจัดการคุณภาพ",      "✅", "INSIGHTS", []),
    NavPage("outcomes",          "Case Outcomes",      "ผลลัพธ์กรณีศึกษา",    "📊", "INSIGHTS", []),
    NavPage("performance",       "Performance",        "การบริหารผล",          "📈", "INSIGHTS", []),
    NavPage("scorecards",        "Scorecards",         "คะแนนชุมชน",          "🏆", "INSIGHTS", []),
    NavPage("reports",           "Reports",            "รายงาน",              "📋", "INSIGHTS", []),

    # AI group
    NavPage("ai_assistant",      "AI Assistant",       "ผู้ช่วย AI",          "🤖", "AI",       []),

    # ADMIN group (restricted)
    NavPage("user_management",   "Users",              "ผู้ใช้งาน",            "👥", "ADMIN",    ["super_admin","province_admin"]),
    NavPage("security_dashboard","Security",           "ความปลอดภัย",         "🔒", "ADMIN",    ["super_admin","province_admin"]),
    NavPage("settings",          "Settings",           "การตั้งค่า",          "⚙️", "ADMIN",    ["super_admin","province_admin"]),
    NavPage("feature_flags",     "Feature Flags",      "Feature Flags",       "🚩", "ADMIN",    ["super_admin"]),
    NavPage("scheduler",         "Scheduler",          "ตัวจัดการงาน",        "⏰", "ADMIN",    ["super_admin","province_admin"]),
    NavPage("backup",            "Backup & Restore",   "สำรองข้อมูล",         "💾", "ADMIN",    ["super_admin"]),
    NavPage("system_health",     "System Health",      "สุขภาพระบบ",          "💚", "ADMIN",    ["super_admin","province_admin"]),
    NavPage("error_tracking",    "Error Tracking",     "ข้อผิดพลาด",          "🐛", "ADMIN",    ["super_admin","province_admin"]),
    NavPage("app_logs",          "App Logs",           "บันทึกแอป",            "📜", "ADMIN",    ["super_admin","province_admin"]),
    NavPage("database_tools",    "Database",           "ฐานข้อมูล",            "🗄️", "ADMIN",    ["super_admin"]),
    NavPage("versioning",        "Version",            "เวอร์ชัน",             "📦", "ADMIN",    ["super_admin","province_admin"]),
    NavPage("audit",             "Audit Log",          "บันทึกตรวจสอบ",       "📋", "ADMIN",    ["super_admin","province_admin"]),

    # HELP group
    NavPage("help_center",       "Help & Guide",       "ความช่วยเหลือ",        "❓", "HELP",     []),
]

# ── Group definitions ─────────────────────────────────────────────────────────
GROUPS = [
    ("HOME",     "🏠", "Home",     "หน้าหลัก"),
    ("PEOPLE",   "👥", "People",   "ประชากร"),
    ("CARE",     "🩺", "Care",     "การดูแล"),
    ("SERVICES", "🤝", "Services", "บริการ"),
    ("MAPS",     "📍", "Maps",     "แผนที่"),
    ("INSIGHTS", "📈", "Insights", "วิเคราะห์"),
    ("AI",       "🧠", "AI",       "ปัญญาประดิษฐ์"),
    ("ADMIN",    "⚙️", "Admin",    "ผู้ดูแล"),
    ("HELP",     "❓", "Help",     "ความช่วยเหลือ"),
]

# ── Role → allowed groups mapping ─────────────────────────────────────────────
ROLE_GROUPS: dict[str, list[str]] = {
    "super_admin":      ["HOME","PEOPLE","CARE","SERVICES","MAPS","INSIGHTS","AI","ADMIN","HELP"],
    "province_admin":   ["HOME","PEOPLE","CARE","SERVICES","MAPS","INSIGHTS","AI","ADMIN","HELP"],
    "district_admin":   ["HOME","PEOPLE","CARE","SERVICES","MAPS","INSIGHTS","AI","HELP"],
    "subdistrict_admin":["HOME","PEOPLE","CARE","SERVICES","MAPS","INSIGHTS","AI","HELP"],
    "volunteer":        ["HOME","PEOPLE","CARE","HELP"],
    "viewer":           ["HOME","PEOPLE","INSIGHTS","HELP"],
}


def get_nav_for_role(role: str, lang: str = "th") -> list[tuple[str, str, list[NavPage]]]:
    """
    Returns: [(group_key, group_label, [NavPage, ...])]
    Filtered for the given role.
    """
    allowed_groups = ROLE_GROUPS.get(role, ["HOME","PEOPLE","CARE","HELP"])
    result = []
    for group_key, group_icon, label_en, label_th in GROUPS:
        if group_key not in allowed_groups:
            continue
        label = label_th if lang == "th" else label_en
        pages = [
            p for p in ALL_PAGES
            if p.group == group_key
            and (not p.roles or role in p.roles)
        ]
        if pages:
            result.append((group_key, f"{group_icon} {label}", pages))
    return result


def get_page_by_key(key: str) -> NavPage | None:
    for p in ALL_PAGES:
        if p.key == key:
            return p
    return None


def get_breadcrumb(page_key: str, lang: str = "th") -> str:
    """Return breadcrumb string: Group > Page"""
    page = get_page_by_key(page_key)
    if not page:
        return ""
    group_map = {g[0]: (g[3] if lang == "th" else g[2]) for g in GROUPS}
    group_label = group_map.get(page.group, page.group)
    page_label = page.label_th if lang == "th" else page.label
    return f"🏠 หน้าหลัก › {group_label} › {page_label}"
