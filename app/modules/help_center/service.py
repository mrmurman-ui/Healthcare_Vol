"""Help Center V2.60 — User guide, FAQ, release notes, version info."""
from __future__ import annotations

import streamlit as st
from app.modules.versioning.service import VERSION_INFO


FAQ = [
    ("วิธีลงทะเบียนประชาชนใหม่", "ไปที่ People › Citizens แล้วคลิกปุ่ม 'Add Citizen' กรอกข้อมูลและบันทึก"),
    ("วิธีบันทึกการเยี่ยมบ้าน", "ไปที่ Care › Home Visits คลิก 'New Visit' เลือกประชาชนและกรอกรายละเอียด"),
    ("วิธีส่งต่อผู้ป่วย", "ไปที่ Care › Referrals คลิก 'New Referral' เลือกผู้ป่วยและสถานพยาบาลปลายทาง"),
    ("วิธีดูรายงานประจำเดือน", "ไปที่ Insights › Reports หรือ Dashboard › Monthly Report แล้วเลือกเดือนและดาวน์โหลด Excel"),
    ("วิธีค้นหาประชาชน", "ใช้ช่องค้นหาด้านบนซ้ายของ sidebar หรือไปที่ People › Citizens และใช้ filter"),
    ("วิธีดู Early Warning", "ไปที่ Care › Early Warning หรือคลิกปุ่ม 'Run Warning Engine' เพื่ออัพเดทการแจ้งเตือน"),
    ("AI สามารถทำอะไรได้บ้าง", "AI สามารถสรุปข้อมูล วิเคราะห์แนวโน้ม และแนะนำแนวทางปฏิบัติ แต่ไม่สามารถวินิจฉัยโรคหรือแนะนำยาได้"),
    ("วิธีเปลี่ยนภาษา", "คลิกที่ปุ่ม 🌐 TH/EN ด้านบนของ sidebar เพื่อสลับภาษา"),
    ("วิธีโหลดข้อมูลทดสอบ", "ไปที่ Admin › System Health แล้วคลิก '🚀 Load Demo Data'"),
    ("วิธีสำรองข้อมูล", "ไปที่ Admin › Backup & Restore แล้วคลิก 'Export All Data'"),
]

WORKFLOWS = [
    {
        "role": "อาสาสมัคร (อสม.)",
        "icon": "🦺",
        "steps": [
            "เข้าสู่ระบบ → แดชบอร์ดแสดงงานที่ต้องทำวันนี้",
            "Care › Home Visits → บันทึกการเยี่ยมบ้าน",
            "Care › Assessments → ประเมินสุขภาพประชาชน",
            "Care › Early Warning → ตรวจสอบการแจ้งเตือน",
            "Care › Referrals → ส่งต่อผู้ป่วยที่ต้องการความช่วยเหลือ",
        ],
    },
    {
        "role": "เจ้าหน้าที่ชุมชน",
        "icon": "👔",
        "steps": [
            "Insights › Executive → ดูภาพรวมสุขภาพชุมชน",
            "People › Citizens → จัดการทะเบียนประชาชน",
            "Services › Projects → ติดตามโครงการชุมชน",
            "Maps › Community Map → ดูแผนที่และ Heatmap",
            "Insights › Reports → สร้างรายงานประจำเดือน",
        ],
    },
    {
        "role": "ผู้บริหาร",
        "icon": "🎯",
        "steps": [
            "Dashboard → AI Executive Summary",
            "Insights › Executive Intel → KPI และแนวโน้ม",
            "Insights › Scorecards → อันดับชุมชน",
            "AI › AI Assistant → สอบถามข้อมูลด้วยภาษาธรรมชาติ",
            "Dashboard › Monthly Report → รายงานประจำเดือน Excel",
        ],
    },
]

RELEASE_NOTES = [
    ("V2.60", "2026", "Enterprise UX & Workflow Redesign — Role-based navigation, Global Search, Quick Actions, Help Center"),
    ("V2.54.2C", "2026", "5-tab Dashboard, Monthly Summary Report with Excel export, AI narrative"),
    ("V2.54.2B", "2026", "Executive Intelligence Center — 13 analytics modules, GIS, Population Pyramid"),
    ("V2.54.2", "2026", "Enterprise login page V2 — animated orbs, Microsoft Fabric inspired"),
    ("V2.54.1B", "2026", "MKI Login page, sidebar blue theme, summary bar, page headers"),
    ("V2.54.1", "2026", "Full RBAC — 10 roles, 152 permissions, user scopes, login history"),
    ("V2.54", "2025", "Production hardening — settings, scheduler, backup, system health, import engine"),
    ("V2.53", "2025", "Population health intelligence — quality management, risk stratification, scorecards"),
    ("V2.51", "2025", "Health monitoring — profiles, assessments, trends, early warning, CVI"),
    ("V2", "2025", "Operations — tasks, follow-ups, announcements, projects, AI assistant"),
    ("V1", "2025", "Core registry — volunteers, households, citizens, home visits, referrals"),
]


def render_help_center() -> None:
    st.markdown("## ❓ Help Center & User Guide")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📖 User Workflows",
        "❓ FAQ",
        "📋 Release Notes",
        "ℹ️ About Platform",
    ])

    # ── Tab 1: User Workflows ─────────────────────────────────────────────────
    with tab1:
        st.markdown("### 🗺️ Daily Workflows by Role")
        st.caption("ขั้นตอนการทำงานรายวันสำหรับแต่ละบทบาท")

        for wf in WORKFLOWS:
            with st.expander(f"{wf['icon']} {wf['role']}"):
                for i, step in enumerate(wf["steps"], 1):
                    st.markdown(
                        f'<div style="display:flex;gap:10px;align-items:start;'
                        f'margin-bottom:8px;">'
                        f'<div style="background:#2563EB;color:white;border-radius:50%;'
                        f'width:22px;height:22px;display:flex;align-items:center;'
                        f'justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;">'
                        f'{i}</div>'
                        f'<div style="font-size:13px;color:#374151;padding-top:2px;">{step}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    # ── Tab 2: FAQ ────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("### ❓ Frequently Asked Questions")
        for question, answer in FAQ:
            with st.expander(f"🔹 {question}"):
                st.info(answer)

    # ── Tab 3: Release Notes ──────────────────────────────────────────────────
    with tab3:
        st.markdown("### 📋 Version History & Release Notes")
        for version, year, notes in RELEASE_NOTES:
            col1, col2 = st.columns([1, 5])
            with col1:
                badge_color = "#2563EB" if version == "V2.60" else "#6B7280"
                st.markdown(
                    f'<div style="background:{badge_color};color:white;'
                    f'border-radius:8px;padding:4px 10px;font-size:12px;'
                    f'font-weight:700;text-align:center;margin-top:4px;">'
                    f'{version}</div>',
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(f"**{year}** — {notes}")

    # ── Tab 4: About ──────────────────────────────────────────────────────────
    with tab4:
        st.markdown("### ℹ️ About MKI Community Health Platform")

        col1, col2 = st.columns(2)
        col1.metric("Platform Version", VERSION_INFO.get("version", "2.60"))
        col2.metric("Environment", VERSION_INFO.get("environment", "production"))

        st.markdown("""
**MKI AI Community Health & Volunteer Operations Platform** is an enterprise-grade
community health management system built for Thailand's public health infrastructure.

**Key Capabilities:**
- 🏥 Complete citizen and household registry
- 🩺 Health monitoring and assessment tracking
- ⚠️ AI-powered early warning system
- 📊 Executive analytics and reporting
- 🗺️ GIS mapping and heatmaps
- 🤖 AI executive summary and insights
- 👥 Full RBAC with 10 user roles

**Technology Stack:** Python 3.12 · Streamlit 1.40 · PostgreSQL · Supabase

**MKI Supplies Co., Ltd.** · Business Consultancy · © 2026 All Rights Reserved

> ⚠️ This platform provides community health operations data only.
> It does not provide medical diagnosis, treatment recommendations, or clinical advice.
""")

        # Quick links
        st.markdown("### 🔗 Quick Links")
        col1, col2, col3 = st.columns(3)
        col1.markdown("[📖 DEPLOYMENT.md](DEPLOYMENT.md)")
        col2.markdown("[🗄️ Database Tools](#)")
        col3.markdown("[💚 System Health](#)")
