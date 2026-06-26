# -*- coding: utf-8 -*-
"""Summary Bar — enterprise KPI cards matching reference design."""
from __future__ import annotations
import streamlit as st
from sqlalchemy import func, select, text
from app.core.db_sync import get_sync_db
import sqlalchemy as sa
from datetime import datetime


@st.cache_data(ttl=120, show_spinner=False)
def _load_summary() -> dict:
    out = {
        "tasks_total": 0, "tasks_completed": 0,
        "tasks_pending": 0, "tasks_overdue": 0,
        "citizens": 0, "volunteers": 0, "alerts": 0,
        "completion_pct": 0,
    }
    try:
        with get_sync_db() as db:
            try:
                from app.modules.tasks.model import Task
                rows = db.execute(
                    select(Task.status, func.count())
                    .where(Task.is_deleted == False)
                    .group_by(Task.status)
                ).all()
                m = {r[0]: r[1] for r in rows}
                out["tasks_total"]     = sum(m.values())
                out["tasks_completed"] = m.get("completed", 0)
                out["tasks_pending"]   = m.get("new", 0) + m.get("assigned", 0) + m.get("in_progress", 0)
                out["tasks_overdue"]   = m.get("overdue", 0)
                total = max(out["tasks_total"], 1)
                out["completion_pct"]  = round(out["tasks_completed"] / total * 100, 1)
            except Exception:
                pass
            try:
                from app.modules.citizens.model import Citizen
                out["citizens"] = db.execute(
                    select(func.count()).select_from(Citizen)
                ).scalar() or 0
            except Exception:
                pass
            try:
                from app.modules.volunteers.model import Volunteer
                out["volunteers"] = db.execute(
                    select(func.count()).select_from(Volunteer)
                    .where(Volunteer.status == "active")
                ).scalar() or 0
            except Exception:
                pass
            try:
                out["alerts"] = db.execute(text(
                    "SELECT COUNT(*) FROM early_warnings WHERE status='open' AND is_deleted=false"
                )).scalar() or 0
            except Exception:
                pass
    except Exception:
        pass
    return out


def render_summary_bar() -> None:
    is_thai = st.session_state.get("lang", "TH") == "TH"
    data    = _load_summary()
    now     = datetime.now()
    time_str = now.strftime(
        f"%d {'ม.ค.ก.พ.มี.ค.เม.ย.พ.ค.มิ.ย.ก.ค.ส.ค.ก.ย.ต.ค.พ.ย.ธ.ค.'.split('.')[now.month-1] if is_thai else now.strftime('%b')} {now.year + (543 if is_thai else 0)} {now.strftime('%H:%M')} {'น.' if is_thai else ''}"
    )

    title   = "ภาพรวมการแจ้งเตือน"             if is_thai else "Alert & Operations Overview"
    subtitle= "สรุปสถานะการแจ้งเตือนและข้อมูลสำคัญในระบบแบบเรียลไทม์" if is_thai else "Real-time summary of alerts and key operational metrics"
    updated = "อัปเดตล่าสุด"                    if is_thai else "Last updated"
    footer  = "ข้อมูลอัปเดตแบบเรียลไทม์ • ปลอดภัย • เชื่อถือได้" if is_thai else "Real-time data • Secure • Reliable"

    lbl_all      = "งานทั้งหมด"    if is_thai else "All Tasks"
    lbl_done     = "เสร็จสิ้น"     if is_thai else "Completed"
    lbl_pending  = "รอดำเนินการ"   if is_thai else "Pending"
    lbl_overdue  = "เกินกำหนด"     if is_thai else "Overdue"
    lbl_citizens = "ประชาชน"       if is_thai else "Citizens"
    lbl_vols     = "อสม."          if is_thai else "Volunteers"

    no_change    = "ไม่มีการเปลี่ยนแปลง" if is_thai else "No change"
    vs_prev      = "เทียบกับช่วงก่อนหน้า" if is_thai else "vs previous period"
    pop_link     = "ข้อมูลประชากรทั้งหมด" if is_thai else "View all population"
    prev_up      = "เพิ่มขึ้นจากช่วงก่อนหน้า" if is_thai else "Increase from previous period"

    pct      = data["completion_pct"]
    overdue  = data["tasks_overdue"]
    alerts   = data["alerts"]

    # Icon SVGs (inline, safe for st.markdown)
    ICONS = {
        "tasks":    '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4A90D9" stroke-width="1.8"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="9" y1="7" x2="15" y2="7"/><line x1="9" y1="11" x2="15" y2="11"/><line x1="9" y1="15" x2="12" y2="15"/></svg>',
        "done":     '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><polyline points="9,12 11,14 15,10"/></svg>',
        "pending":  '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="6" x2="12" y2="12"/><line x1="12" y1="12" x2="16" y2="14"/></svg>',
        "overdue":  '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="1.8"><polygon points="12,2 22,20 2,20"/><line x1="12" y1="9" x2="12" y2="13"/><circle cx="12" cy="16" r="0.5" fill="#EF4444"/></svg>',
        "citizens": '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="1.8"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>',
        "vols":     '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="1.8"><circle cx="9" cy="7" r="3"/><circle cx="15" cy="7" r="3"/><path d="M1 20c0-3.3 3.1-6 7-6"/><path d="M23 20c0-3.3-3.1-6-7-6"/><path d="M8 20c0-3.3 1.8-6 4-6s4 2.7 4 6"/></svg>',
    }

    def bg(color: str) -> str:
        colors = {
            "blue":   "#EFF6FF", "green": "#F0FDF4",
            "amber":  "#FFFBEB", "red":   "#FEF2F2",
            "purple": "#F5F3FF",
        }
        return colors.get(color, "#F8FAFF")

    def card(icon_key, label, value, color,
             sub_html="", footer_html="", extra_html="") -> str:
        return f"""
<div style="background:white;border-radius:16px;padding:22px 20px 16px;
  box-shadow:0 2px 12px rgba(15,23,42,0.06),0 0 0 1px #F1F5F9;
  display:flex;flex-direction:column;gap:0;min-width:0;flex:1;">
  <div style="width:48px;height:48px;border-radius:50%;background:{bg(color)};
    display:flex;align-items:center;justify-content:center;margin-bottom:14px;">
    {ICONS[icon_key]}
  </div>
  <div style="font-size:15px;font-weight:500;color:#64748B;margin-bottom:6px;
    display:flex;align-items:center;gap:6px;">{label}
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" stroke-width="2">
      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  </div>
  <div style="font-size:36px;font-weight:800;color:#0F172A;line-height:1;margin-bottom:8px;">
    {f"{value:,}" if isinstance(value,int) else value}
  </div>
  {sub_html}
  {footer_html}
  {extra_html}
</div>"""

    # Sub-texts
    def neutral_sub(txt):
        return f'<div style="font-size:12px;color:#94A3B8;">— &nbsp;{txt}</div>'

    def green_sub(val, txt):
        return f'<div style="font-size:13px;color:#22C55E;font-weight:600;margin-bottom:2px;">↑ {val}%</div><div style="font-size:12px;color:#94A3B8;">{txt}</div>'

    def red_sub(val, txt):
        return f'<div style="font-size:13px;color:#EF4444;font-weight:600;margin-bottom:2px;">↑ {val}</div><div style="font-size:12px;color:#94A3B8;">{txt}</div>'

    def blue_btn(txt):
        return f'<div style="margin-top:10px;"><span style="background:#EFF6FF;color:#2563EB;border:1px solid #BFDBFE;font-size:12px;font-weight:600;padding:6px 12px;border-radius:8px;cursor:pointer;">📊 {txt}</span></div>'

    c1 = card("tasks",    lbl_all,     data["tasks_total"],     "blue",   neutral_sub(no_change))
    c2 = card("done",     lbl_done,    data["tasks_completed"], "green",  green_sub(pct, vs_prev) if pct > 0 else neutral_sub(no_change))
    c3 = card("pending",  lbl_pending, data["tasks_pending"],   "amber",  neutral_sub(no_change))
    c4 = card("overdue",  lbl_overdue, overdue,                 "red",    neutral_sub(no_change))
    c5 = card("citizens", lbl_citizens,data["citizens"],        "purple", "", blue_btn(pop_link))
    c6 = card("vols",     lbl_vols,    data["volunteers"],      "purple",
              red_sub(f"⚠️ {alerts}", prev_up) if alerts > 0 else neutral_sub(no_change))

    st.markdown(f"""
<div style="background:white;border-radius:20px;padding:28px 32px 20px;
  box-shadow:0 4px 24px rgba(15,23,42,0.07),0 0 0 1px #E8ECF0;margin-bottom:24px;">

  <!-- Header row -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px;">
    <div>
      <div style="font-size:22px;font-weight:800;color:#0F172A;margin-bottom:6px;">{title}</div>
      <div style="font-size:14px;color:#64748B;">{subtitle}</div>
    </div>
    <div style="text-align:right;flex-shrink:0;margin-left:20px;">
      <div style="display:flex;align-items:center;gap:6px;justify-content:flex-end;margin-bottom:3px;">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5">
          <polyline points="1,4 1,10 7,10"/><path d="M3.5,15a9,9,0,1,0,.5-4.5"/>
        </svg>
        <span style="font-size:13px;font-weight:600;color:#2563EB;">{updated}</span>
      </div>
      <div style="font-size:13px;color:#64748B;">{time_str}</div>
    </div>
  </div>

  <!-- KPI Cards -->
  <div style="display:flex;gap:14px;flex-wrap:nowrap;">
    {c1}{c2}{c3}{c4}{c5}{c6}
  </div>

  <!-- Footer -->
  <div style="margin-top:20px;padding-top:16px;border-top:1px solid #F1F5F9;
    text-align:center;font-size:13px;color:#94A3B8;">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94A3B8"
      stroke-width="2" style="vertical-align:middle;margin-right:4px;">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    </svg>
    {footer}
  </div>

</div>
""", unsafe_allow_html=True)
