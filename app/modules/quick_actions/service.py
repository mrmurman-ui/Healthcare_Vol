"""Quick Actions V2.60 — 100% native Streamlit, zero HTML."""
from __future__ import annotations
import streamlit as st

QUICK_ACTIONS = [
    ("citizens",           "👤", "New Citizen",       "ลงทะเบียนประชาชน"),
    ("home_visits",        "🏠", "New Home Visit",    "บันทึกการเยี่ยมบ้าน"),
    ("referrals",          "📤", "New Referral",      "ส่งต่อผู้ป่วย"),
    ("health_assessments", "📏", "New Assessment",    "ประเมินสุขภาพ"),
    ("tasks",              "✅", "New Task",          "สร้างงานใหม่"),
    ("early_warning",      "⚠️", "Run Alerts",        "ตรวจสอบการแจ้งเตือน"),
    ("ai_assistant",       "🤖", "AI Summary",        "สรุปรายงาน AI"),
    ("reports",            "📋", "Reports",           "ส่งออกรายงาน"),
]


def render_quick_actions() -> str | None:
    is_thai = st.session_state.get("lang", "TH") == "TH"
    st.subheader("⚡ " + ("ดำเนินการด่วน" if is_thai else "Quick Actions"))
    st.caption("เลือกสิ่งที่ต้องการทำ" if is_thai else "Jump to common actions instantly")
    st.divider()

    open_lbl = "เปิด →" if is_thai else "Open →"

    for row_start in range(0, len(QUICK_ACTIONS), 4):
        row = QUICK_ACTIONS[row_start:row_start + 4]
        cols = st.columns(4)
        for col, (page_key, icon, label_en, label_th) in zip(cols, row):
            label = label_th if is_thai else label_en
            with col:
                # Pure native Streamlit — no HTML at all
                st.write(f"{icon} **{label}**")
                if st.button(open_lbl, key=f"qa_{page_key}",
                             use_container_width=True, type="primary"):
                    return page_key
        st.write("")

    return None
