# -*- coding: utf-8 -*-
"""MKI Community Health Platform — V2.60 Fixed"""
from __future__ import annotations
import traceback
import streamlit as st

st.set_page_config(
    page_title="MKI Community Health Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load Noto Sans Thai fonts as base64 and inject into CSS
import os as _os, base64 as _b64

def _load_font_css() -> str:
    """Read woff2 files and embed as base64 data URIs — works with any Streamlit path."""
    _font_dir = _os.path.join(_os.path.dirname(__file__), "static", "fonts")
    _weights = [("300","Light"),("400","Regular"),("500","Medium"),
                ("600","SemiBold"),("700","Bold"),("800","ExtraBold")]
    _css = ""
    for _w, _ in _weights:
        _path = _os.path.join(_font_dir, f"NotoSansThai-{_w}.woff2")
        if _os.path.exists(_path) and _os.path.getsize(_path) > 1000:
            with open(_path, "rb") as _f:
                _data = _b64.b64encode(_f.read()).decode()
            _css += (
                f"@font-face {{font-family:\'Noto Sans Thai\';font-weight:{_w};"
                f"font-style:normal;font-display:swap;"
                f"src:url(\'data:font/woff2;base64,{_data}\') format(\'woff2\')}}"
            )
    return _css

_FONT_CSS = _load_font_css()

st.markdown("""
<style>
""" + _FONT_CSS + """


/* Apply Noto Sans Thai globally to every element */
*, *::before, *::after,
html, body, [class*="css"],
.stApp, .main, .stMarkdown,
.stTextInput input, .stTextArea textarea,
.stSelectbox div, .stButton > button,
.stDataFrame, .stTable, p, span, div,
.stCaption, .stMetric, label, h1, h2, h3, h4,
[data-testid="stSidebar"] * {
    font-family: 'Noto Sans Thai', 'Noto Sans', -apple-system, sans-serif !important;
}
/* ── Sidebar dark navy ── */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg,
        rgba(11,27,94,0.92) 0%,
        rgba(29,78,216,0.85) 40%,
        rgba(37,99,235,0.80) 70%,
        rgba(30,64,175,0.88) 100%) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid rgba(255,255,255,0.12) !important;
    box-shadow: 4px 0 24px rgba(11,27,94,0.3) !important;
}
[data-testid="stSidebar"],
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.9) !important; }

/* Group labels — readable white caps */
[data-testid="stSidebar"] .stCaption p {
    font-size: 22px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    color: rgba(255,255,255,0.90) !important;
    margin: 16px 0 4px 2px !important;
    padding: 0 !important;
}

/* Nav buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    text-align: left !important;
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.55) !important;
    padding: 5px 14px !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    border-radius: 8px !important;
    margin: 1px 0 !important;
    transition: all 0.15s !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.09) !important;
    color: #fff !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg,rgba(37,99,235,0.35),rgba(37,99,235,0.2)) !important;
    color: #fff !important;
    font-weight: 700 !important;
    border-left: 3px solid #60A5FA !important;
    padding-left: 9px !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
    margin: 6px 0 !important;
}

/* ── Sidebar search input — force white text at ALL levels ── */
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextInput input:hover,
[data-testid="stSidebar"] .stTextInput input:active,
[data-testid="stSidebar"] .stTextInput input:focus,
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="base-input"] input,
[data-testid="stSidebar"] [data-baseweb="input"] > div > input,
[data-testid="stSidebar"] input[type="text"],
[data-testid="stSidebar"] input[type="search"] {
    background: rgba(255,255,255,0.14) !important;
    border: 1px solid rgba(255,255,255,0.30) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: #ffffff !important;
    font-size: 13px !important;
    font-family: 'Noto Sans Thai', sans-serif !important;
}
[data-testid="stSidebar"] .stTextInput input:focus,
[data-testid="stSidebar"] [data-baseweb="input"] input:focus,
[data-testid="stSidebar"] input[type="text"]:focus {
    background: rgba(255,255,255,0.22) !important;
    border-color: rgba(255,255,255,0.55) !important;
    box-shadow: 0 0 0 2px rgba(255,255,255,0.18) !important;
    outline: none !important;
}
[data-testid="stSidebar"] .stTextInput input::placeholder,
[data-testid="stSidebar"] [data-baseweb="input"] input::placeholder,
[data-testid="stSidebar"] input[type="text"]::placeholder {
    color: rgba(255,255,255,0.50) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.50) !important;
}
[data-testid="stSidebar"] .stTextInput input::selection {
    background: rgba(255,255,255,0.30) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
/* Hide label (already hidden but ensure) */
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stTextInput > label {
    display: none !important;
}
/* BaseWeb container background */
[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-baseweb="base-input"] {
    background: rgba(255,255,255,0.14) !important;
    border-color: rgba(255,255,255,0.30) !important;
}

/* Language buttons */
[data-testid="stSidebar"] .stButton > button[key*="lang"] {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 20px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    color: #fff !important;
    padding: 5px 12px !important;
    text-align: center !important;
}

/* ── Main area ── */
.stApp {
    background: linear-gradient(160deg,#F8FAFF 0%,#EFF6FF 50%,#F8FAFF 100%) !important;
}
.main .block-container {
    padding-top: 12px !important;
    max-width: 1400px !important;
}

/* Breadcrumb pill */
.breadcrumb-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #64748B;
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 5px 12px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    cursor: pointer;
}
.breadcrumb-pill:hover { background: #EFF6FF; border-color: #BFDBFE; }

/* Metric cards */
[data-testid="metric-container"] {
    background: white !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}

/* Primary buttons in main */
.main .stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#0F2167 0%,#1D4ED8 55%,#2563EB 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 16px rgba(15,33,103,0.35) !important;
}
/* Login sign-in button */
[data-testid="stButton"][data-key="mki_signin"] > button {
    background: linear-gradient(135deg,#0F2167 0%,#1D4ED8 55%,#2563EB 100%) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; height:52px !important;
    font-size:15px !important; font-weight:700 !important;
}

/* Page titles — all heading levels */
.main h1, .main h2, .main h3,
.main h1 *, .main h2 *, .main h3 *,
[data-testid="stHeading"],
[data-testid="stHeadingWithActionElements"],
[data-testid="stHeadingWithActionElements"] * {
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #1E3A8A !important;
    line-height: 1.4 !important;
}
/* Hide anchor link icon next to headings */
[data-testid="stHeadingWithActionElements"] a,
.main h1 a, .main h2 a, .main h3 a {
    display: none !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list" {
    background: white;
    border-radius: 12px 12px 0 0;
    border-bottom: 2px solid #EFF6FF;
    gap: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── Auth ───────────────────────────────────────────────────────────────────────
from app.modules.auth.page import render_login
from app.modules.auth.session import get_current_user, is_authenticated, logout_user
from app.modules.navigation.role_navigation_service import (
    get_nav_for_role, get_breadcrumb, get_page_by_key
)
from app.shared.page_header import render_page_header

if not is_authenticated():
    render_login()
    st.stop()

user = get_current_user()

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("lang","TH"),("page","dashboard"),
              ("prev_page",None),("recent_pages",[]),("favorites",[])]:
    if k not in st.session_state:
        st.session_state[k] = v

def nav_to(key: str) -> None:
    prev = st.session_state.get("page")
    if prev != key:
        st.session_state["prev_page"] = prev
    st.session_state["page"] = key
    recent = st.session_state.get("recent_pages", [])
    if key in recent:
        recent.remove(key)
    recent.insert(0, key)
    st.session_state["recent_pages"] = recent[:20]

is_thai = st.session_state["lang"] == "TH"

# Strings
S = {
    "TH": {
        "search_ph": "ค้นหา... ประชาชน งาน หน้า",
        "logout": "ออกจากระบบ",
        "back": "← ย้อนกลับ",
        "recent": "🕐 เพิ่งดู",
        "favorites": "⭐ รายการโปรด",
        "no_recent": "ยังไม่มีประวัติการเข้าชม",
        "no_favs": "ยังไม่มีรายการโปรด",
        "add_fav": "⭐ เพิ่มหน้านี้ใน Favorites",
        "added_fav": "เพิ่มแล้ว!",
        "search_results": "ผลการค้นหา",
        "no_results": "ไม่พบผลลัพธ์",
    },
    "EN": {
        "search_ph": "Search... citizens, tasks, pages",
        "logout": "Logout",
        "back": "← Back",
        "recent": "🕐 Recent",
        "favorites": "⭐ Favorites",
        "no_recent": "No recent pages yet",
        "no_favs": "No favorites yet",
        "add_fav": "⭐ Add to Favorites",
        "added_fav": "Added!",
        "search_results": "Search Results",
        "no_results": "No results found",
    },
}
T = S[st.session_state["lang"]]

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Header with MKI Logo ────────────────────────────────────────────────
    import os as _os
    _logo_path = _os.path.join(_os.path.dirname(__file__), "assets", "mki_logo_b64.txt")
    _logo_b64 = ""
    try:
        with open(_logo_path, encoding="utf-8") as _lf:
            _logo_b64 = _lf.read().strip()
    except Exception:
        pass

    if _logo_b64:
        logo_html = (
            f'<div style="display:flex;align-items:center;gap:10px;padding:4px 0;">'
            f'<div style="width:44px;height:44px;border-radius:12px;overflow:hidden;'
            f'background:rgba(255,255,255,0.18);backdrop-filter:blur(12px);'
            f'-webkit-backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.3);'
            f'box-shadow:0 4px 12px rgba(11,27,94,0.3);flex-shrink:0;">'
            f'<img src="{_logo_b64}" style="width:44px;height:44px;object-fit:contain;"></div>'
            f'<div><div style="font-size:14px;font-weight:800;color:white;line-height:1.2;">MKI Health</div>'
            f'<div style="font-size:11px;color:rgba(255,255,255,0.55);">{user.full_name[:22]}</div>'
            f'<div style="font-size:10px;color:rgba(255,255,255,0.4);">{user.role}</div></div>'
            f'</div>'
        )
    else:
        logo_html = (
            f'<div style="display:flex;align-items:center;gap:10px;padding:4px 0;">'
            f'<div style="width:44px;height:44px;border-radius:12px;'
            f'background:rgba(255,255,255,0.18);backdrop-filter:blur(12px);'
            f'border:1px solid rgba(255,255,255,0.3);display:flex;align-items:center;'
            f'justify-content:center;font-size:22px;flex-shrink:0;">🏥</div>'
            f'<div><div style="font-size:14px;font-weight:800;color:white;line-height:1.2;">MKI Health</div>'
            f'<div style="font-size:11px;color:rgba(255,255,255,0.55);">{user.full_name[:22]}</div>'
            f'<div style="font-size:10px;color:rgba(255,255,255,0.4);">{user.role}</div></div>'
            f'</div>'
        )
    st.markdown(logo_html, unsafe_allow_html=True)

    st.divider()

    # ── Language toggle ────────────────────────────────────────────────────────
    lc1, lc2 = st.columns(2)
    with lc1:
        if st.button("🇹🇭 ภาษาไทย" if not is_thai else "✅ ภาษาไทย",
                     key="lang_th", use_container_width=True,
                     type="primary" if is_thai else "secondary"):
            if not is_thai:
                st.session_state["lang"] = "TH"
                st.rerun()
    with lc2:
        if st.button("🇬🇧 English" if is_thai else "✅ English",
                     key="lang_en", use_container_width=True,
                     type="primary" if not is_thai else "secondary"):
            if is_thai:
                st.session_state["lang"] = "EN"
                st.rerun()

    st.divider()

    # ── Global search ──────────────────────────────────────────────────────────
    search_q = st.text_input(
        "search", placeholder=T["search_ph"],
        key="sidebar_search", label_visibility="collapsed",
    )
    if search_q and len(search_q.strip()) >= 2:
        from app.modules.global_search.service import search_all
        results = search_all(search_q)
        if results:
            for grp, items in list(results.items())[:3]:
                st.caption(grp)
                for item in items[:3]:
                    lbl = f"{item['tag']} {item['label']}" if item.get("tag") else item["label"]
                    if st.button(lbl, key=f"sr_{item['key']}_{item['label'][:6]}",
                                 use_container_width=True):
                        nav_to(item["key"])
                        st.rerun()
        else:
            st.caption(T["no_results"])

    st.divider()

    # ── Role-based navigation ──────────────────────────────────────────────────
    current_page = st.session_state.get("page", "dashboard")
    lang_code = "th" if is_thai else "en"
    nav_groups = get_nav_for_role(user.role, lang_code)

    for group_key, group_label, pages in nav_groups:
        st.markdown(
            f'<p style="font-size:22px;font-weight:700;color:rgba(255,255,255,0.95);'
            f'margin:16px 0 4px 2px;padding:0;line-height:1.3;">{group_label}</p>',
            unsafe_allow_html=True,
        )
        for page in pages:
            label = page.label_th if is_thai else page.label
            is_active = current_page == page.key
            if st.button(
                f"{page.icon} {label}",
                key=f"nav_{page.key}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                nav_to(page.key)
                st.rerun()

    st.divider()

    # ── Logout ─────────────────────────────────────────────────────────────────
    if st.button(f"🚪 {T['logout']}", use_container_width=True):
        logout_user()
        st.rerun()

# ── MAIN AREA ─────────────────────────────────────────────────────────────────
page_key = st.session_state.get("page", "dashboard")
prev_page = st.session_state.get("prev_page")

# Back button + Breadcrumb row
bc_col, btn_col = st.columns([6, 1])
with bc_col:
    breadcrumb = get_breadcrumb(page_key, lang_code)
    if breadcrumb:
        st.markdown(
            f'<div class="breadcrumb-pill">{breadcrumb}</div>',
            unsafe_allow_html=True,
        )
with btn_col:
    if prev_page and prev_page != page_key:
        prev_info = get_page_by_key(prev_page)
        prev_label = (prev_info.label_th if is_thai else prev_info.label) if prev_info else prev_page
        if st.button(T["back"], key="back_btn", help=f"Back to {prev_label}"):
            st.session_state["page"] = prev_page
            st.session_state["prev_page"] = None
            st.rerun()

# Page header
render_page_header(page_key)

# Summary bar — dashboard only
if page_key == "dashboard":
    from app.shared.summary_bar import render_summary_bar
    render_summary_bar()

# ── ROUTING ────────────────────────────────────────────────────────────────────
try:
    if page_key == "dashboard":
        from app.modules.dashboard.page import render_dashboard; render_dashboard()
    elif page_key == "volunteers":
        from app.modules.volunteers.page import render_volunteers; render_volunteers()
    elif page_key == "households":
        from app.modules.households.page import render_households; render_households()
    elif page_key == "citizens":
        # ── Ensure CA codes assigned (injected fix) ───────────────────────────
        try:
            from app.core.db_sync import get_sync_db as _gsd
            from sqlalchemy import text as _t2
            with _gsd() as _db:
                _mr = _db.execute(_t2(
                    "SELECT citizen_code FROM citizens WHERE citizen_code LIKE 'CA%' "
                    "ORDER BY citizen_code DESC LIMIT 1"
                )).fetchone()
                _s = 1
                if _mr and _mr[0]:
                    try: _s = int(_mr[0][2:]) + 1
                    except: pass
                _nc = _db.execute(_t2(
                    "SELECT id FROM citizens WHERE citizen_code IS NULL OR citizen_code=''"
                )).fetchall()
                for _i, _r in enumerate(_nc):
                    _db.execute(_t2(
                        "UPDATE citizens SET citizen_code=:c WHERE id=:id "
                        "AND (citizen_code IS NULL OR citizen_code='')"
                    ), {"c": f"CA{_s+_i:05d}", "id": str(_r[0])})
        except Exception:
            pass
        from app.modules.citizens.page import render_citizens; render_citizens()
    elif page_key == "home_visits":
        from app.modules.home_visits.page import render_home_visits; render_home_visits()
    elif page_key == "referrals":
        from app.modules.referrals.page import render_referrals; render_referrals()
    elif page_key == "gis":
        from app.modules.gis.page import render_gis; render_gis()
    elif page_key == "reports":
        from app.modules.reports.page import render_reports; render_reports()
    elif page_key == "audit":
        from app.modules.audit.page import render_audit; render_audit()
    elif page_key == "tasks":
        from app.modules.tasks.service import render_tasks; render_tasks()
    elif page_key == "followups":
        from app.modules.followups.service import render_followups; render_followups()
    elif page_key == "announcements":
        from app.modules.announcements.service import render_announcements; render_announcements()
    elif page_key == "projects":
        from app.modules.community_projects.service import render_community_projects; render_community_projects()
    elif page_key == "analytics":
        from app.modules.analytics.service import render_analytics; render_analytics()
    elif page_key == "ai_assistant":
        from app.modules.ai_assistant.service import render_ai_assistant; render_ai_assistant()
    elif page_key == "notifications":
        from app.modules.notifications.service import render_notifications; render_notifications()
    elif page_key == "health_profiles":
        from app.modules.health_profiles.service import render_health_profiles; render_health_profiles()
    elif page_key == "health_assessments":
        from app.modules.health_assessments.service import render_health_assessments; render_health_assessments()
    elif page_key == "health_trends":
        from app.modules.health_trends.service import render_health_trends; render_health_trends()
    elif page_key == "elderly_monitoring":
        from app.modules.community_health.service import render_elderly_monitoring; render_elderly_monitoring()
    elif page_key == "early_warning":
        from app.modules.early_warning.service import render_early_warning; render_early_warning()
    elif page_key == "cvi":
        from app.modules.early_warning.service import render_cvi; render_cvi()
    elif page_key == "community_health":
        from app.modules.community_health.service import render_community_health; render_community_health()
    elif page_key == "health_analytics":
        from app.modules.community_health.service import render_health_analytics; render_health_analytics()
    elif page_key == "quality_management":
        from app.modules.quality_management.service import render_quality_management; render_quality_management()
    elif page_key == "outcomes":
        from app.modules.outcomes.service import render_outcomes; render_outcomes()
    elif page_key == "performance":
        from app.modules.performance_management.service import render_performance_management; render_performance_management()
    elif page_key == "scorecards":
        from app.modules.community_scorecards.service import render_community_scorecards; render_community_scorecards()
    elif page_key == "population_health":
        from app.modules.population_health.service import render_population_health; render_population_health()
    elif page_key == "risk_stratification":
        from app.modules.risk_stratification.service import render_risk_stratification; render_risk_stratification()
    elif page_key == "capacity_planning":
        from app.modules.capacity_planning.service import render_capacity_planning; render_capacity_planning()
    elif page_key == "executive":
        from app.modules.executive_command_center.service import render_executive_command_center; render_executive_command_center()
    elif page_key == "executive_v2":
        from app.modules.analytics_v2.executive_v2 import render_executive_v2; render_executive_v2()
    elif page_key == "settings":
        from app.modules.settings.service import render_settings; render_settings()
    elif page_key == "feature_flags":
        from app.modules.feature_flags.service import render_feature_flags; render_feature_flags()
    elif page_key == "scheduler":
        from app.modules.scheduler.service import render_scheduler; render_scheduler()
    elif page_key == "backup":
        from app.modules.backup_restore.service import render_backup_restore; render_backup_restore()
    elif page_key == "system_health":
        from app.modules.system_health.service import render_system_health; render_system_health()
    elif page_key == "error_tracking":
        from app.modules.error_tracking.service import render_error_tracking; render_error_tracking()
    elif page_key == "app_logs":
        from app.modules.application_logs.service import render_application_logs; render_application_logs()
    elif page_key == "database_tools":
        from app.modules.database_tools.service import render_database_tools; render_database_tools()
    elif page_key == "versioning":
        from app.modules.versioning.service import render_versioning; render_versioning()
    elif page_key == "import_engine":
        from app.modules.import_engine.service import render_import_engine; render_import_engine()
    elif page_key == "user_management":
        from app.modules.user_management.page import render_user_management; render_user_management()
    elif page_key == "security_dashboard":
        from app.modules.security_dashboard.service import render_security_dashboard; render_security_dashboard()
    elif page_key == "quick_actions":
        from app.modules.quick_actions.service import render_quick_actions
        result = render_quick_actions()
        if result:
            nav_to(result)
            st.rerun()
    elif page_key == "help_center":
        from app.modules.help_center.service import render_help_center; render_help_center()
    elif page_key == "workspace":
        st.subheader("🖥️ " + ("พื้นที่ทำงาน" if is_thai else "My Workspace"))
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**" + ("🕐 เพิ่งดู" if is_thai else "🕐 Recent Pages") + "**")
            recent = st.session_state.get("recent_pages", [])
            if recent:
                for rk in recent[:10]:
                    p = get_page_by_key(rk)
                    if p:
                        lbl = p.label_th if is_thai else p.label
                        if st.button(f"{p.icon} {lbl}", key=f"rec_{rk}",
                                     use_container_width=True):
                            nav_to(rk)
                            st.rerun()
            else:
                st.info("ยังไม่มีประวัติการเข้าชม" if is_thai else "No recent pages yet.")
        with c2:
            st.markdown("**" + ("⭐ รายการโปรด" if is_thai else "⭐ Favorites") + "**")
            favs = st.session_state.get("favorites", [])
            if favs:
                for fk in favs:
                    p = get_page_by_key(fk)
                    if p:
                        lbl = p.label_th if is_thai else p.label
                        if st.button(f"⭐ {p.icon} {lbl}", key=f"fav_{fk}",
                                     use_container_width=True):
                            nav_to(fk)
                            st.rerun()
            else:
                st.info("ยังไม่มีรายการโปรด" if is_thai else "No favorites yet.")
            add_lbl = "⭐ " + ("เพิ่มหน้านี้" if is_thai else "Add Current Page")
            if st.button(add_lbl, key="add_fav_btn", type="primary"):
                rec = st.session_state.get("recent_pages", [])
                if len(rec) > 1 and rec[1] not in favs:
                    favs.append(rec[1])
                    st.session_state["favorites"] = favs
                    st.success("✅ " + ("เพิ่มแล้ว" if is_thai else "Added!"))
                    st.rerun()
    elif page_key == "campaigns":
        from app.modules.campaigns.service import render_campaigns; render_campaigns()
    else:
        st.info(f"{'หน้า' if is_thai else 'Page'} '{page_key}' — {'กำลังพัฒนา' if is_thai else 'Coming soon'}.")

except Exception as e:
    st.error(f"❌ {e}")
    with st.expander("Error Details"):
        st.code(traceback.format_exc())
